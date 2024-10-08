import h5py
import matplotlib.pyplot as plt

# mở cái h5 lên
with h5py.File('luu_thong_so_jump_nojump.h5', 'r') as file:
    # Truy cập các bộ dữ liệu trong tệp và trích xuất dữ liệu
    jump_memory = file['jump_memory'][:]
    no_jump_memory = file['no_jump_memory'][:]

# Vẽ đồ thị dữ liệu
plt.figure()
plt.plot(jump_memory, label='Bộ nhớ nhảy')
plt.plot(no_jump_memory, label='Bộ không nhớ nhảy')
plt.xlabel('Tình trạng')
plt.ylabel('sức chịu')
plt.legend()
plt.title('Sơ đồ game khủng long')
plt.show()
