# Experiment Index — module4

> **反向索引**：tag → 事件編號 / 檔案 → 事件編號。
> 由 `log_experiment.py` 自動維護（每筆事件寫完後追加/更新此檔）。
> 人類也可手動編輯補 tag。
> 目的：AI 快速查「上次類似問題怎麼處理」、「這支程式改過哪些事」。

## Tags → Events

*（範例格式：`- #aws → #13, #14, #15`）*

- #init → #1
- #athena #glue #s3 #create-database #external-table → #2
- #athena #preview-table #cloudtrail #grader-pitfall → #3
- #athena #bucketizing #jan-table #performance → #4
- #athena #parquet #partitioning #creditcard #performance → #5
- #athena #views #cctrips #cashtrips #comparepay #grader-pitfall → #6
- #cloudformation #athena #named-query #iac → #7
- #iam #policy-for-data-scientists #mary #least-privilege #named-query → #8
## Files → Events（程式檔 ↔ 改動它的事件）

*（範例格式：`- src/clean.py → #7, #12`）*
- d:/p/awshomework/作業要求/module4/athenaquery.cf.yml → #7
## Phases → Events 範圍

- Phase 1 — <名稱>：#1 ~ *（封存後會標明結尾編號）*

---

## 維護規則

- `log_experiment.py` 寫完一筆事件，會把該事件的 `Tags` 欄位 + `對應輸出檔案` 欄位反向索引到這裡
- tag 命名：小寫、hyphen-case、`#` 開頭
- 若多筆事件共用 tag，**按事件編號升冪**列
- Phase 封存時，把「事件編號範圍」寫到 `Phases → Events` 段
