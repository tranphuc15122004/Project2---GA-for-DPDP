# GA + VNS for Dynamic Pickup and Delivery Problem (DPDP)

## 1. Input

### 1.1 Road Network Graph `G(F, A)`
- **F** = {Fᵢ | i = 1, ..., M} là tập hợp các nhà máy (nodes).  
- **A** = {aᵢⱼ | i, j ∈ M} là tập hợp các cung (edges), trong đó mỗi aᵢⱼ chứa:
  - **dᵢⱼ**: khoảng cách giữa Fᵢ và Fⱼ.
  - **tᵢⱼ**: thời gian di chuyển giữa Fᵢ và Fⱼ.

Mỗi nhà máy có một số lượng **dock** giới hạn để tiếp nhận và dỡ hàng. Nếu không còn dock trống, xe phải **chờ** đến khi có dock được giải phóng.

- **Dock approaching time**: Thời gian cố định từ khi xe đến nhà máy đến khi tiếp cận được dock.

### 1.2 Orders Set `O`
- **O** = {oᵢ | i = 1, ..., N}, với mỗi oᵢ là một đơn hàng gồm:
  - **Fᵢp, Fᵢd**: điểm nhận và điểm giao hàng.
  - **qᵢ** = (q_standard, q_small, q_box): số lượng tấm tiêu chuẩn, tấm nhỏ và hộp.
    - 1 tấm tiêu chuẩn = 2 tấm nhỏ = 4 hộp.
  - **tie**: thời điểm khởi tạo đơn hàng.
  - **til**: thời điểm yêu cầu hoàn thành đơn hàng.

- **Loading/Unloading time**: Ví dụ nếu có `q` tấm tiêu chuẩn, thời gian tải/dỡ:
  - `td = q × w` với `w = 180 giây/tấm`.

### 1.3 Homogeneous Vehicles `V`
- **V** = {vₖ | k = 1, ..., K}
  - Mỗi xe có dung tích chứa hàng cố định.
  - Vị trí xuất phát của mỗi xe là ngẫu nhiên.

## 2. Constraints

1. **Hoàn thành đơn hàng**: Mọi đơn hàng phải được phục vụ đúng điểm nhận và giao.
2. **Đúng thời hạn**: Đơn hàng phải hoàn thành trong khoảng [tie, til]. Trễ → phạt.
3. **Chia nhỏ đơn hàng**:
   - Được phép nếu vượt quá tải trọng xe.
   - Không được tách rời đơn vị nhỏ nhất (pallet tiêu chuẩn, nhỏ, hộp).
4. **Sức chứa xe**: Không vượt quá tải trọng tối đa Q. Ví dụ: 12 pallet tiêu chuẩn/xe.
5. **Ca làm việc tài xế**: Ví dụ: 08:30–12:00 và 13:30–18:00.
6. **Ràng buộc LIFO (Last In First Out)**:
   - Nếu xe phục vụ nhiều đơn hàng, hàng lấy sau phải giao trước.
   - Ví dụ:
     - `F₁p → F₂p → F₁d → F₂d` → **vi phạm LIFO**
     - `F₁p → F₂p → F₂d → F₁d` → **hợp lệ**
7. **Số lượng dock giới hạn**:
   - Nếu có nhiều xe đến hơn số dock, xe phải chờ.
8. **Quy tắc "đến trước phục vụ trước"**:
   - Khi có nhiều xe chờ và dock trống, hệ thống chọn ngẫu nhiên 1 xe.

## 3. Objective Function

### 3.1 Tối thiểu hóa tổng thời gian trễ:
```
f1 = ∑_{i = 1}^{N} max(0, aᵢ𝒹 - til)
```
- `aᵢ𝒹`: thời điểm thực tế đơn hàng `i` được hoàn thành.

### 3.2 Tối thiểu hóa quãng đường trung bình của xe:
```
f2 = (1 / K) × ∑_{k = 1}^{K} ∑_{i = 1}^{lₖ - 1} d(nₖᵢ, nₖᵢ₊₁)
```
- `nₖᵢ`: điểm thứ `i` trong lộ trình của xe `vₖ`.

### 3.3 Hàm mục tiêu tổng hợp:
```
f = λ × f1 + f2
```
- `λ`: một hệ số lớn nhằm ưu tiên tối thiểu hóa độ trễ đơn hàng.

## 4. Giải thuật Genetic algorithm kết hợp Variable Neighborhood Search


Trong bài toán DPDP tại mỗi thời điểm t, các đơn hàng mới sẽ xuất hiện một cách động. Để xây dựng lời giải phù hợp trong khoảng thời gian xử lý ΔT, chúng tôi sử dụng một biến thể của Genetic Algorithm (GA) kết hợp giữa quá trình lai ghép định hướng độ trễ, tìm kiếm cục bộ (Local Search) và quá trình chọn lọc elitist. Phương pháp này giúp cải thiện lời giải một cách hiệu quả trong mỗi khoảng thời gian.

### 1. Khởi tạo lời giải

Tại thời điểm t, thuật toán tiến hành thu thập các thông tin sau:

- **O(t)**: tập các đơn hàng mới được tiết lộ.
- **R(t−1)**: lời giải tốt nhất tại thời điểm trước đó.

Sau đó:

- Các đơn hàng trong O(t) được chèn vào lời giải R(t−1) bằng thuật toán chèn vị trí tốt nhất, tạo thành lời giải khởi đầu R(t).
- Tập các cặp pickup–delivery hợp lệ (gọi là super node) được trích xuất và sắp xếp ngẫu nhiên để tạo ra quần thể ban đầu P={p1,...,pN}.

### 2. Cơ chế lai ghép hướng độ trễ

Mỗi lời giải là một tập các tuyến đường của K xe. Trong bước lai ghép:

- Tính toán độ trễ của từng tuyến đường từ hai cha mẹ.
- Chọn các tuyến đường tốt hơn (độ trễ thấp hơn) để xây dựng lời giải con.
- Xử lý trùng lặp đơn hàng bằng cách loại bỏ đơn hàng trùng khỏi tuyến đường có độ trễ cao hơn.
- Phân bổ lại các đơn hàng bị mất bằng cách chèn vào vị trí thích hợp trong các tuyến.

Quá trình này cho phép tạo ra lời giải mới có chất lượng tốt hơn, đồng thời vẫn đảm bảo tính đa dạng.

### 3. Tối ưu cục bộ (Local Search)

Sau mỗi bước lai ghép, lời giải con sẽ được cải thiện bằng 4 phép Local Search sau:

- **Couple Exchange**: hoán đổi hai cặp pickup–delivery giữa các tuyến khác nhau.
- **Block Exchange**: trao đổi hai đoạn liên tiếp giữa hai tuyến.
- **Block Relocate**: di chuyển một đoạn liên tiếp từ tuyến này sang tuyến khác.
- **Multi-Couple Relocate**: di chuyển nhiều cặp pickup–delivery giữa các tuyến.

Các phép này giúp tinh chỉnh lời giải để giảm độ trễ, rút ngắn quãng đường hoặc cân bằng tải giữa các tuyến.

### 4. Chọn lọc và tiêu chí dừng

Sau khi tạo ra tập lời giải con Q, thuật toán tiến hành:

- Chọn N lời giải tốt nhất từ tập P∪Q để hình thành quần thể mới.
- Ghi nhận lời giải tốt nhất trong quần thể hiện tại làm R(t).

Thuật toán sẽ dừng nếu:

- Đạt đến số vòng lặp tối đa **GMAX**, hoặc
- Không có cải thiện nào cho lời giải tốt nhất trong **G_stagnant** vòng lặp liên tiếp.

### 5. Mã giả thuật toán

```plaintext
Algorithm framework : GA + VNS for DPDP

/* O(t) is a set of unstarted orders.*/
/* R(t - 1) is the best route plant at t - 1 .*/
/* P denotes the population */
/* Q denotes the offspring */

O(t) ← Collect_orders(t)  
R(t - 1) ← Restore_last_solution()	
R(t) ← Dispatch_new_order(O(t) , R(t -1))

P = {p1 , p2 , … , pN} ← Initialize_population(R(t - 1), O(t))
Q ← ∅

for iter = 1 to GMAX do
	for i = 1 to N do
		Randomly choose two parent solutions pj, pk from P.
		p′ ← Crossover(pj, pk)
		Q ← Q ∪ p′
	end for

	Choose the best N solutions from P ∪ Q to form the new population P

	for all pl in P:
		p ← Local_search(p)
    
	Record the best solution of P as R(t).
	if more than G_stagnant can’t improve the best solution R(t)
        then break
end for
```
