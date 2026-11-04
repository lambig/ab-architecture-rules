# 固定版の公開

公開前に実装・導入例・README・Javadocを同じ版で確認し、`sh verify-example.sh` を通します。
`build.gradle`、例のGradle/POM、READMEの版を揃えます。既に公開された版の上書きはできません。

1. 対象コミットを固定し、公開する全ファイルとPOM・sources・Javadocを確認します。
2. 公開用の署名鍵とパスワードを `SIGNING_KEY` / `SIGNING_PASSWORD` 環境変数へ設定します。Gradle標準の外部署名設定も利用できます。リポジトリへ保存しません。
3. `sh gradlew clean test -PreleaseBundle centralBundle` で署名付きbundleを生成します。
   出力は `build/central/ab-architecture-rules-<版>-central.zip` です。署名がない場合は生成に失敗します。
4. [Central Publisher Portalの手順](https://central.sonatype.org/publish/publish-portal-upload/)に従い、
   所有するnamespaceへbundleを登録・検証・公開します。認証と署名鍵の管理は公開担当者が行います。
5. Maven Centralから固定版を取得できることを `sh verify-example.sh public` で確認し、同じ版を利用するABServiceの回帰を確認します。
6. 公開に対応するコミットへ `v<版>` タグを付けます。初回公開後はREADMEの未公開表示を更新します。

候補版の成功と公開版の取得成功は別の確認です。公開待ちの座標へ切り替えたABServiceのPRは、取得可能になるまでマージしません。
ライブラリとその利用側に同じ実装を複製することや、利用側のソースからライブラリをビルドする代替経路は設けません。
