import os
import sys
import glob
import time
import getpass
from dotenv import load_dotenv
import snowflake.connector

# Ensure UTF-8 output encoding for Windows terminal compatibility
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# SETTING: Đặt số lượng file muốn push thử.
# Đặt MAX_FILES = 1 để thử 1 file đầu tiên.
# Đặt MAX_FILES = None hoặc 0 để push toàn bộ.
MAX_FILES = None


def main():
    # 1. Load environment variables from .env
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path=env_path)

    sf_account = os.getenv("SNOWFLAKE_ACCOUNT", "")
    sf_user = os.getenv("SNOWFLAKE_USER", "")
    sf_password = os.getenv("SNOWFLAKE_PASSWORD", "").strip()
    sf_role = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")
    sf_warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
    sf_database = os.getenv("SNOWFLAKE_DATABASE", "DBT_DB")
    sf_schema = os.getenv("SNOWFLAKE_SCHEMA", "DBT_SCHEMA")

    if not sf_account or not sf_user:
        print("[ERROR] SNOWFLAKE_ACCOUNT hoặc SNOWFLAKE_USER chưa được thiết lập trong file .env!")
        sys.exit(1)

    if not sf_password:
        print("[WARNING] SNOWFLAKE_PASSWORD chưa được thiết lập trong file .env!")
        try:
            sf_password = getpass.getpass("Vui lòng nhập mật khẩu Snowflake của bạn: ").strip()
        except Exception:
            sf_password = ""

        if not sf_password:
            print("\n[ERROR] Lỗi: Chưa có mật khẩu Snowflake. Vui lòng nhập SNOWFLAKE_PASSWORD vào file .env và thử lại!")
            sys.exit(1)

    print("==================================================")
    print("Bắt đầu kết nối và đẩy dữ liệu lên Snowflake Cloud")
    print(f"Account   : {sf_account}")
    print(f"User      : {sf_user}")
    print(f"Role      : {sf_role}")
    print(f"Database  : {sf_database}")
    print(f"Warehouse : {sf_warehouse}")
    print(f"Schema    : {sf_schema}")
    print(f"Max Files : {MAX_FILES if MAX_FILES else 'ALL (Toàn bộ)'}")
    print("==================================================")

    # 2. Connect to Snowflake
    try:
        conn = snowflake.connector.connect(
            user=sf_user,
            password=sf_password,
            account=sf_account,
            role=sf_role
        )
        cursor = conn.cursor()
        print("[SUCCESS] Kết nối Snowflake thành công!")
    except Exception as e:
        print(f"[ERROR] Kết nối Snowflake thất bại: {e}")
        sys.exit(1)

    try:
        # 3. Setup Warehouse, Database, Schema
        print("\nĐang kiểm tra / khởi tạo Warehouse, Database và Schema...")
        cursor.execute(f"CREATE WAREHOUSE IF NOT EXISTS {sf_warehouse} WITH WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE INITIALLY_SUSPENDED = TRUE;")
        cursor.execute(f"USE WAREHOUSE {sf_warehouse};")

        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {sf_database};")
        cursor.execute(f"USE DATABASE {sf_database};")

        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {sf_schema};")
        cursor.execute(f"USE SCHEMA {sf_schema};")

        # 4. Create Table BANHANG
        print("Tạo bảng BANHANG (nếu chưa có)...")
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS BANHANG (
            THOI_GIAN VARCHAR(20),
            MA_GIAO_DICH VARCHAR(50),
            CHI_NHANH VARCHAR(200),
            THOI_GIAN_GIAO_DICH VARCHAR(50),
            TONG_TIEN_HANG FLOAT,
            DOANH_THU_GIAO_DICH FLOAT,
            TONG_GIA_VON FLOAT,
            LOI_NHUAN_GOP FLOAT,
            MA_HANG VARCHAR(50),
            TEN_HANG VARCHAR(500),
            NHOM_HANG VARCHAR(500),
            SO_LUONG FLOAT,
            GIA_BAN_SP FLOAT,
            DOANH_THU FLOAT,
            GIA_VON_SP FLOAT
        );
        """
        cursor.execute(create_table_sql)

        # 5. Create Stage for CSV staging
        print("Tạo Stage internal BANHANG_STAGE...")
        cursor.execute("""
            CREATE STAGE IF NOT EXISTS BANHANG_STAGE
            FILE_FORMAT = (
                TYPE = 'CSV'
                FIELD_OPTIONALLY_ENCLOSED_BY = '"'
                SKIP_HEADER = 1
                EMPTY_FIELD_AS_NULL = TRUE
                FIELD_DELIMITER = ','
                ENCODING = 'UTF-8'
            );
        """)

        # 6. Find CSV files in the data directory
        base_dir = os.path.join(os.path.dirname(__file__), "data")
        all_csv_files = sorted(glob.glob(os.path.join(base_dir, "*.csv")))

        if not all_csv_files:
            print(f"[WARNING] Không tìm thấy file CSV nào trong {base_dir}")
            sys.exit(1)

        csv_files = all_csv_files[:MAX_FILES] if MAX_FILES else all_csv_files
        print(f"\nTìm thấy {len(all_csv_files)} file CSV. Sẽ xử lý {len(csv_files)} file...")

        # 7. PUT files to Stage
        start_time = time.time()
        for idx, file_path in enumerate(csv_files, 1):
            normalized_path = file_path.replace("\\", "/")
            file_name = os.path.basename(file_path)
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"  [{idx}/{len(csv_files)}] Đang đẩy file: {file_name} ({file_size_mb:.1f} MB) ...", end=" ", flush=True)
            put_sql = f"PUT 'file://{normalized_path}' @BANHANG_STAGE AUTO_COMPRESS=TRUE OVERWRITE=TRUE PARALLEL=4;"
            cursor.execute(put_sql)
            print("Done [OK]")

        put_duration = time.time() - start_time
        print(f"\nHoàn thành đẩy {len(csv_files)} file lên Stage trong {put_duration:.2f} giây.")

        # 8. Copy data from Stage into Table
        print("\nBắt đầu nạp dữ liệu từ Stage vào bảng BANHANG (COPY INTO)...")
        copy_start = time.time()
        copy_sql = """
            COPY INTO BANHANG
            FROM @BANHANG_STAGE
            FILE_FORMAT = (
                TYPE = 'CSV'
                FIELD_OPTIONALLY_ENCLOSED_BY = '"'
                SKIP_HEADER = 1
                EMPTY_FIELD_AS_NULL = TRUE
                FIELD_DELIMITER = ','
                ENCODING = 'UTF-8'
            )
            ON_ERROR = 'CONTINUE';
        """
        cursor.execute(copy_sql)
        copy_duration = time.time() - copy_start
        print(f"Hoàn thành COPY INTO trong {copy_duration:.2f} giây.")

        # 9. Verify total rows loaded
        cursor.execute("SELECT COUNT(*) FROM BANHANG;")
        total_rows = cursor.fetchone()[0]
        print(f"\n==================================================")
        print(f"[SUCCESS] ĐÃ ĐẨY THÀNH CÔNG DỮ LIỆU LÊN SNOWFLAKE!")
        print(f"Bảng        : {sf_database}.{sf_schema}.BANHANG")
        print(f"Tổng bản ghi: {total_rows:,} dòng")
        print(f"==================================================")

    except Exception as e:
        print(f"\n[ERROR] Lỗi trong quá trình xử lý Snowflake: {e}")
    finally:
        cursor.close()
        conn.close()
        print("Đã đóng kết nối Snowflake.")


if __name__ == "__main__":
    main()
