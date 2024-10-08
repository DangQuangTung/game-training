import h5py

def check_h5_file(file_path):
    try:
        with h5py.File(file_path, 'r') as file:
            print("File {} là hợp lệ.".format(file_path))
            print("Khóa tập dữ liệu:")
            for key in file.keys():
                print(key)
    except OSError:
        print("File {} không hợp lệ hoặc không tồn tại.".format(file_path))

# Đường dẫn đến file .h5 cần kiểm tra
file_path = 'luu_thong_so_jump_nojump.h5'

# Kiểm tra file .h5
check_h5_file(file_path)

# T giải thích cho ae hiểu đây 
# hàm check_h5_file được tạo ra để kiểm tra tính hợp lệ của file .h5. 
# Nếu file tồn tại và không gây lỗi khi mở, nó sẽ in ra thông báo "File [đường dẫn file] là hợp lệ." 
# và liệt kê các khóa của tập tin .h5. 
# Nếu file không hợp lệ hoặc không tồn tại, nó sẽ in ra thông báo "File [đường dẫn file] không hợp lệ hoặc không tồn tại."