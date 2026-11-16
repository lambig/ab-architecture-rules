# Shipping starter

`sh gradlew clean check run` で公開ライブラリの利用とアクセス境界を確認します。JDK 17以上でbuildし、アプリケーションはJava 11以上を対象とします。
正常時の出力は `H1 boundary passed` と `dispatch: ready` です。

toolboxは通常依存、ab-architecture-rules・ArchUnit・JUnitはテスト依存です。版は `gradle.properties` に固定しています。
規則は専用遷移の直接呼出し・メソッド参照を操作内に限定します。注釈漏れ・import範囲外・reflection・業務順序は保証しません。
自分のpackageへ移す場合は `BoundaryCheck` のimport範囲を更新してください。

取得元とファイルのハッシュは `skeleton-source.json` にあります。その `sourceCommit` に固定した
`https://github.com/lambig/ab-architecture-rules/blob/<sourceCommit>/skeleton/README.md` が導入・違反の修正・更新手順です。
テンプレートの再生成は空の別ディレクトリへ行い、既存の変更と比較して取り込んでください。
