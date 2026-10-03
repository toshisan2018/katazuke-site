# 内部リンク強化 設計メモ

目的：関連ページ同士をつないで回遊性とSEO評価（クロール・文脈）を高める。
`docs/improvement-plan.md` フェーズ1。ライブ反映は各ページの本文（カスタムHTML）やナビで。

## 現状
- 各サービスページに「関連ページ」カードあり、ヘッダー/フッターに主要リンクあり（良好）。
- 弱い点：**コラム記事 ↔ サービスページ**の相互リンク、**サービス ↔ 市区町村ページ**、**お困りごと系（akiya/gomiyashiki/hikkoshi/tenpo）からの導線**が不足しがち。

## 推奨リンクマップ（まだ弱い所を補う）
| このページから | ここへリンク（追加推奨） |
|---|---|
| トップ | 各サービス（済）＋ 対応エリア ＋ 主要コラム |
| 家の片付け(katazuke) | 生前整理 / 空き家 / 不用品回収 / 料金 / コラム「空き家・実家の片付け方」 |
| 不用品回収(fuyouhin) | 対応品目(hinmoku) / 家電の処分(コラム) / 料金 / 引っ越し |
| 残置物撤去(zanchibutsu) | 解体サイト(既設バナー) / 空き家 / 会社概要 |
| 生前整理・遺品整理(seiri) | コラム「生前整理」「遺品整理」/ 空き家 / 料金 |
| 空き家(akiya) | 残置物撤去 / 解体サイト / コラム「空き家・実家の片付け方」 |
| ゴミ屋敷(gomiyashiki-katazuke) | コラム「ゴミ屋敷の片付け方」/ 不用品回収 / 料金 |
| 引っ越し(hikkoshi) | 不用品回収 / コラム「引っ越しの不用品」「家電の処分」 |
| 店舗・オフィス(tenpo) | 倉庫・工場(souko) / 残置物撤去 / コラム「店舗・オフィス閉店」 |
| 各コラム記事 | 対応する**サービスページ**＋関連コラム（記事末に必ず） |
| 各サービス | 対応する**市区町村ページ**（公開後） |

## 貼り付け用：関連リンクブロック（自己完結・どのページにも流用可）
本文末尾の「カスタムHTML」ブロックに貼り、`<li>` を各ページの文脈に合わせて差し替え。

```html
<div style="max-width:860px;margin:24px auto;font-family:'Noto Sans JP','Hiragino Kaku Gothic ProN','Yu Gothic',Meiryo,sans-serif;">
  <h2 style="font-size:18px;font-weight:900;color:#2a2724;margin:0 0 10px;border-left:5px solid #f7b500;padding-left:10px;">あわせて読みたい</h2>
  <ul style="list-style:none;margin:0;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:8px;">
    <li><a href="/fuyouhin/" style="display:block;border:1px solid #e0a000;border-radius:8px;padding:10px;text-decoration:none;color:#9a6a00;font-weight:700;background:#fff;">不用品回収について →</a></li>
    <li><a href="/seiri/" style="display:block;border:1px solid #e0a000;border-radius:8px;padding:10px;text-decoration:none;color:#9a6a00;font-weight:700;background:#fff;">生前整理・遺品整理 →</a></li>
    <li><a href="/ryoukin/" style="display:block;border:1px solid #e0a000;border-radius:8px;padding:10px;text-decoration:none;color:#9a6a00;font-weight:700;background:#fff;">料金・費用について →</a></li>
    <li><a href="/akiya-katazuke/" style="display:block;border:1px solid #e0a000;border-radius:8px;padding:10px;text-decoration:none;color:#9a6a00;font-weight:700;background:#fff;">コラム：空き家・実家の片付け方 →</a></li>
  </ul>
</div>
```

## コラム記事からの導線（最優先の抜け）
各コラム記事の**末尾に、対応するサービスページへのCTA付きリンク**を必ず置く（例：
- 「空き家・実家の片付け方」→ `/akiya/`・`/katazuke/`
- 「不用品回収の費用」→ `/fuyouhin/`・`/ryoukin/`
- 「ゴミ屋敷の片付け方」→ `/gomiyashiki-katazuke/`
- 「農機具買取のコツ」→ `/nouki-kaitori/`
- 「店舗・オフィス閉店」→ `/tenpo/`）
→ コラムで集客 → サービスページへ送客 → 問い合わせ、の流れを作る。

## ナビ／フッター
- 市区町村ページ公開後は、`/area/`（対応エリア）ページから各市ページへリンク一覧を設置。
- フッターの「サービス」「ご案内」リンクは現状維持でOK。

## 注意
- リンクは**文脈に合うものだけ**（無関係な大量リンクは逆効果）。
- これはrepo上の設計メモ。反映は各ページ本文（カスタムHTML）で手動、またはWordPress接続時に代行。
