# Hybird metaheuristics for Dynamic Pickup and Delivery Problem (DPDP)

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

## 4. Genetic algorithm kết hợp Variable Neighborhood Search


Trong bài toán DPDP tại mỗi thời điểm t, các đơn hàng mới sẽ xuất hiện một cách động. Để xây dựng lời giải phù hợp trong khoảng thời gian xử lý ΔT, chúng tôi sử dụng một biến thể của Genetic Algorithm (GA) kết hợp giữa quá trình lai ghép định hướng độ trễ, tìm kiếm cục bộ (Local Search) và quá trình chọn lọc elitist. Phương pháp này giúp cải thiện lời giải một cách hiệu quả trong mỗi khoảng thời gian.

### 4.1. Khởi tạo lời giải

Tại thời điểm t, thuật toán tiến hành thu thập các thông tin sau:

- **O(t)**: tập các đơn hàng mới được tiết lộ.
- **R(t−1)**: lời giải tốt nhất tại thời điểm trước đó.

Sau đó:

- Các đơn hàng trong O(t) được chèn vào lời giải R(t−1) bằng thuật toán chèn vị trí tốt nhất, tạo thành lời giải khởi đầu R(t).
- Tập các cặp pickup–delivery hợp lệ (gọi là super node) được trích xuất và sắp xếp ngẫu nhiên để tạo ra quần thể ban đầu P={p1,...,pN}.

### 4.2. Cơ chế lai ghép hướng độ trễ

Mỗi lời giải là một tập các tuyến đường của K xe. Trong bước lai ghép:

- Tính toán độ trễ của từng tuyến đường từ hai cha mẹ.
- Chọn các tuyến đường tốt hơn (độ trễ thấp hơn) để xây dựng lời giải con.
- Xử lý trùng lặp đơn hàng bằng cách loại bỏ đơn hàng trùng khỏi tuyến đường có độ trễ cao hơn.
- Phân bổ lại các đơn hàng bị mất bằng cách chèn vào vị trí thích hợp trong các tuyến.

Quá trình này cho phép tạo ra lời giải mới có chất lượng tốt hơn, đồng thời vẫn đảm bảo tính đa dạng.

### 4.3. Tối ưu cục bộ (Local Search)

Sau mỗi bước lai ghép, lời giải con sẽ được cải thiện bằng 4 phép Local Search sau:

- **Couple Exchange**: hoán đổi hai cặp pickup–delivery giữa các tuyến khác nhau.
- **Block Exchange**: trao đổi hai đoạn liên tiếp giữa hai tuyến.
- **Block Relocate**: di chuyển một đoạn liên tiếp từ tuyến này sang tuyến khác.
- **Multi-Couple Relocate**: di chuyển nhiều cặp pickup–delivery giữa các tuyến.

Các phép này giúp tinh chỉnh lời giải để giảm độ trễ, rút ngắn quãng đường hoặc cân bằng tải giữa các tuyến.

### 4.4. Chọn lọc và tiêu chí dừng

Sau khi tạo ra tập lời giải con Q, thuật toán tiến hành:

- Chọn N lời giải tốt nhất từ tập P∪Q để hình thành quần thể mới.
- Ghi nhận lời giải tốt nhất trong quần thể hiện tại làm R(t).

Thuật toán sẽ dừng nếu:

- Đạt đến số vòng lặp tối đa **GMAX**, hoặc
- Không có cải thiện nào cho lời giải tốt nhất trong **G_stagnant** vòng lặp liên tiếp.

### 4.5. Mã giả thuật toán

```plaintext
Algorithm: GA + VNS for DPDP

1.  O(t) ← Collect_orders(t)                   # O(t) is a set of unstarted orders
2.  R(t - 1) ← Restore_last_solution()
3.  R(t) ← Initialization(O(t), R(t - 1))
4.  P ← Population_initialization(R(t - 1), O(t))
5.  Q ← ∅
6.  R* ← R(t), f* ← fitness(R(t)), gen ← 0

7.  For iter = 1 to G_max:
8.      While |Q| < N:
9.          Randomly choose two parent solutions p_j, p_k from P
10.         p ← Crossover(p_j, p_k)
11.         Q ← Q ∪ {p}
12.     P ← P ∪ Q
13.     Keep N best solutions in P
14.     For each p in P:
15.         p ← Local_search(p_j, p_k)
16.     Sort P by fitness

17.     If fitness(P[0]) < f*:
18.         R* ← P[0]
19.         f* ← fitness(P[0])
20.         gen ← 0
21.     Else:
22.         gen ← gen + 1

23.     If gen > G_stagnant or timeout:
24.         Break

25. R(t) ← R*
```

## 5. Ant Colony Algorithm kết hợp Variable Neighborhood Search


Trong bài toán DPDP tại mỗi thời điểm t, các đơn hàng mới sẽ xuất hiện một cách động. Để xây dựng lời giải phù hợp trong khoảng thời gian xử lý ΔT, chúng tôi sử dụng một biến thể của Genetic Algorithm (GA) kết hợp giữa quá trình lai ghép định hướng độ trễ, tìm kiếm cục bộ (Local Search) và quá trình chọn lọc elitist. Phương pháp này giúp cải thiện lời giải một cách hiệu quả trong mỗi khoảng thời gian.

### 5.1. Khởi tạo lời giải

Tại thời điểm t, thuật toán tiến hành thu thập các thông tin sau:

- **O(t)**: tập các đơn hàng mới được tiết lộ.
- **R(t−1)**: lời giải tốt nhất tại thời điểm trước đó.

Sau đó:

- Các đơn hàng trong O(t) được chèn vào lời giải R(t−1) bằng thuật toán chèn vị trí tốt nhất, tạo thành lời giải khởi đầu R(t).
- Tập các cặp pickup–delivery hợp lệ (gọi là super node) được trích xuất và sắp xếp ngẫu nhiên để tạo ra quần thể ban đầu P={p1,...,pN}.


### 5.2 Ma trận Pheromone và Heuristic


- **Ma trận pheromone** được khởi tạo với kích thước n x n, trong đó n là số lượng node trong các đơn hàng chưa xử lý. Mỗi cặp node được gán giá trị pheromone mặc định (0.1) để đảm bảo tìm kiếm không bị thiên vị và duy trì đa dạng.

- **Ma trận heuristic** phản ánh độ hấp dẫn giữa các cặp node, được tính theo công thức:

    heuristic(n, v) = 1 / (distance(n, v) + time(n, v))

  Trong đó:
  - `distance(n, v)` là khoảng cách giữa node n và v.
  - `time(n, v)` là thời gian di chuyển giữa node n và v.

  Giá trị heuristic sau đó được chuẩn hóa về khoảng [0.1, 1.0] để hướng dẫn thuật toán ACO ưu tiên các lựa chọn có chi phí thấp hơn.

### 5.3. Xây dựng lời giải
Thuật toán **Construct Solution** tạo ra một lời giải khả thi cho bài toán định tuyến xe động với các cặp điểm nhận - giao hàng (DPDP). Thuật toán đảm bảo các ràng buộc:

- Mỗi cặp điểm nhận-giao được phục vụ bởi cùng một xe.
- Điểm nhận hàng phải đến trước điểm giao hàng.
- Tuân thủ nguyên tắc **LIFO** (Last In First Out).
- Không vượt quá tải trọng và thời gian phục vụ.

1. **Khởi tạo kế hoạch**:
   - Sao chép kế hoạch tuyến cơ sở hiện tại (`base_plan`).
   - Trộn ngẫu nhiên các cặp node chưa gán (`unassigned_pairs`).

2. **Lặp gán node vào tuyến**:
   - Tính **độ hấp dẫn** giữa node `n` và xe `v` dựa trên pheromone và heuristic:
     $$ A(n, v) = \tau(n, v)^\alpha \cdot \eta(n, v)^\beta $$
   - Chọn cặp `(v, n)` dựa theo **xác suất lựa chọn** (Roulette Wheel):
     $$ P(v, n) = \frac{A(n, v)}{\sum_{v', n'} A(n', v')} $$
   - Gán node được chọn vào tuyến của xe tương ứng.

3. **Kiểm tra tính khả thi**:
   - Kiểm tra ràng buộc: tải trọng, thứ tự nhận-giao, LIFO, v.v.
   - Nếu vi phạm, cố gắng sửa chữa lời giải. Nếu không thể, loại bỏ.

4. **Trả về lời giải**:
   - Đóng gói kế hoạch thành một `chromosome`, đại diện cho một cá thể trong GA hoặc ACO.


### 5.4. Cập nhật pheromone

Sau mỗi vòng lặp, thuật toán cập nhật ma trận pheromone \( \tau \) theo 3 bước:

1. **Bay hơi pheromone**:
   Giảm pheromone trên mọi cạnh để làm mờ lựa chọn cũ:
   $$
   \tau(e) \gets \max(\tau_{\text{min}}, \tau(e) \cdot (1 - \rho))
   $$

2. **Tăng cường pheromone**:
   Các kiến tốt nhất (elite ants) bổ sung pheromone theo chất lượng lời giải:
   $$
   \Delta\tau(e) = w \cdot \frac{1}{\text{fitness}}, \quad
   \tau(e) \gets \min(\tau_{\text{max}}, \tau(e) + \Delta\tau(e))
   $$

3. **Chuẩn hóa pheromone**:
   Đảm bảo mọi giá trị `tau(e)` nằm trong khoảng `[tau_min, tau_max]` để giữ ổn định tối ưu.

Cơ chế này giúp cân bằng giữa **khai thác lời giải tốt** và **khám phá phương án mới** trong quá trình giải bài toán DPDP bằng ACO.

### 5.5. Variable Neighborhood Search
Sau khi tìm được lời giải tốt từ ACO, thuật toán VNS được sử dụng để cải thiện thêm bằng cách áp dụng tuần tự các phép biến đổi cục bộ như `inter_couple_exchange`, `block_exchange`, `block_relocate`, `multi_pd_group_relocate`, và `2-opt`. Quá trình lặp tiếp tục cho đến khi không còn cải thiện nào. VNS giúp nâng cao chất lượng lời giải trong khi vẫn đảm bảo các ràng buộc DPDP như cùng xe, thứ tự nhận-giao, và LIFO.

### 5.6. Mã giả thuật toán

```plaintext
Algorithm: ACO + VNS for DPDP

1.  O(t) ← Collect_orders(t)         # O(t) is a set of unstarted orders
2.  R(t - 1) ← Restore_last_solution()
3.  R(t) ← Initialization(O(t), R(t - 1))
4.  S ← Build_supernode_map(O(t))
5.  τ ← Initialize_pheromone(S)
6.  η ← Calculate_heuristic(τ)
7.  R* ← R(t), f* ← ∞, gen ← 0

8.  For iter = 1 to G_max:
9.      A ← ∅                         # List of ant solutions
10.     While |A| < N:
11.         r ← Construct_solution(S, τ, η)
12.         If r ≠ ∅:
13.             A ← A ∪ {r}
14.     Update_pheromone(τ, A)
15.     Sort A by fitness
16.     If fitness(A[0]) < f*:
17.         R* ← A[0]
18.         f* ← fitness(A[0])
19.         gen ← 0
20.     Else:
21.         gen ← gen + 1
22.     If gen > G_stagnant or timeout:
23.         Break

24. R(t) ← R*
25. R(t) ← Variable_neighborhood_search(R(t))
```

## Hướng dẫn sử dụng
1. **Chuyển về thư mục gốc của dự án**  
   Mở terminal và điều hướng đến thư mục chứa mã nguồn:

   ```bash
   cd /path/to/project
2. **Cài đặt các thư viện phụ thuộc**  
    ```bash
   pip install -r requirements.txt

3. **Khởi chạy ứng dụng**  

    Sử dụng lệnh sau để khởi chạy API và giao diện người dùng:

    ```bash
    python main.py --api

3. **Truy cập giao diện web**  
    Sau khi ứng dụng khởi chạy thành công, mở trình duyệt và truy cập địa chỉ:
    ```bash
    http://192.168.1.20:5000
