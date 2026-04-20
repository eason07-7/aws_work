# TASKS — module4

> **未來 + 現在**的任務清單。過去的事件看 `JOURNAL.md`；當下快照看 `CHECKPOINT.md`。
> 原則：Phase 是粗顆粒階段目標，每個 Phase 有驗收條件、待辦、待決。

## Phase 1 — <階段名稱>（進行中）

### 驗收條件（Phase 結束必須達成）

- [ ] *（請使用者填：例如「資料清洗管線能跑完一個月份」、「MCP server 通過 smoke test」）*

### 待辦

- [ ] *（具體可驗證的小任務；完成時打勾並可附事件編號如 `（#3）`）*
- [ ] *（每項理想上對應一筆事件記錄）*

### 待決（阻塞中）

- [ ] *（需使用者決定的題目；例如「要不要改 AWS region」）*

### Followup（Phase 結束前要收尾）

- [ ] *（Phase 收尾時掃一次：文件、測試、封存實驗記錄）*

---

## Phase 2 — <規劃中>

### 目標

*（一句話：這個 Phase 要達成什麼狀態）*

### 前置條件

- Phase 1 驗收條件全部打勾

---

## 已完成 Phase（封存摘要）

*（Phase 結束後寫 1-2 行結論，詳情在 `experiments/phaseN_<name>.md`）*

尚無。

---

## 寫法備註

- 每項打勾時可加事件編號：`- [x] 清洗 202603（#7）`
- 待決項目若因某事件產生，也標：`- [ ] 改 region？（起因 #15）`
- Phase 切換時機：驗收條件全打勾 → rename 目前的 `JOURNAL.md` 成 `experiments/phaseN_<name>.md` → 新建空的 `JOURNAL.md` → 在此檔把目前 Phase 搬到「已完成 Phase」
- `TASKS.md` 人類為主、AI 為輔維護（AI 應提議、不擅自刪）
