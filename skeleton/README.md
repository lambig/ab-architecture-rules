# 公開依存で始めるSkeleton

Gradleの独立プロジェクトを空のディレクトリへ生成し、toolboxの利用と、明示的に採用したアクセス境界規則を確認します。
アプリケーションの最低Javaは11、buildにはJDK 17以上が必要です。Harness本体の最低Java 8は変更しません。
汎用Quarkus基盤や実運用の設定は含みません。Mavenを選ぶ場合のHarness単独例は既存の `example/` を参照してください。

## 固定版の取得

Git、Python 3.9以上、JDK 17以上を用意します。`SOURCE` にはレビューしたSkeletonの40桁のコミットSHAを指定します。
タグを使う場合も、参照先のSHAを確認して固定します。`main` の移動を更新として自動追従しません。

```sh
git clone --no-checkout https://github.com/lambig/ab-architecture-rules.git template-source
cd template-source
git checkout --detach "$SOURCE"
python3 skeleton/create.py --source "$SOURCE" --output ../my-project
cd ../my-project
git init
git add .
git commit -m "Import pinned Skeleton"
sh gradlew --no-daemon --console=plain clean check run
```

生成物は元checkoutを参照しません。`skeleton-source.json` に取得元SHAと各ファイルのSHA-256を残します。
既存ファイルがあるディレクトリは拒否し、生成内容はコミット済みファイルから取得します。
wrapper、`gradle.properties` のtoolbox 0.4.0とHarness 0.1.0、JUnitの版は固定されています。
ローカルMavenや候補リポジトリを使用せず、Maven Centralから解決します。

正常時は `H1 boundary passed` と `dispatch: ready` が表示されます。
生成したCIはJDK 17でbuildし、`-PruntimeJavaHome` にJava 11の場所を指定して `clean check run` を実行します。
依存更新後も、テストとアプリケーションを最低対応Javaで実行できることを確認します。
Harness・ArchUnit・JUnitはテスト依存だけで、アプリケーションのruntimeに含まれないことを `check` で確認します。
業務型・注釈・packageは利用側の `example.shipping` にあります。自分のpackageへ移す場合は検査のimport範囲も合わせてください。

## 違反と修正

`Main` 内の操作経由の呼出しを `new Shipment().dispatch()` に変えると、`check` が失敗します。
`Runnable call = new Shipment()::dispatch` も操作外の参照取得として失敗します。
診断には `expected caller class`、呼出元、`Shipment.dispatch` が現れます。依存取得やコンパイルの失敗とは区別してください。
呼出しを `DispatchOperation` へ戻して `clean check run` を実行すると成功します。検査の無効化や失敗無視で修正を代用しません。
既存の `example/src/scenarios/` と `BoundaryCheck` がこの例の規則と違反fixtureの正本です。

注釈漏れ、import範囲外、reflection、業務順序、transaction、値の妥当性は検出しません。
操作内で取得した参照を外へ返すことも許可します。保証の詳細はリポジトリのREADMEの「検出範囲と限界」を参照してください。

## 依存とテンプレートの更新

依存更新は `gradle.properties` の版を変更し、通常操作と許容→直接呼出し違反→参照違反→修正を再確認します。
受け入れスクリプトは実在するtoolbox 0.3.1から0.4.0への更新を検証します。Harnessは公開版0.1.0を維持します。
異なる意味の業務規則や最低Javaの変更まで互換とみなさず、更新先の契約を確認してください。

テンプレート更新は、旧SHAと新SHAを別のcheckoutへ固定して、それぞれ空のディレクトリへ生成します。
両生成物の差分と `skeleton-source.json` を比較し、自分の変更と競合する箇所を判断して取り込みます。
既存プロジェクトへ生成コマンドを上書き実行しません。wrapper・CI・設定・注釈・import範囲の変更を含めて確認し、
依存更新と同じ操作を再実行します。初回Skeletonには旧公開テンプレートがないため、この手順を異なる公開版間で実行した証拠はまだありません。
依存更新の成功をテンプレート更新や全プロジェクトの受け入れの証拠に代えません。

## 受け入れの再実行

```sh
python3 skeleton/verify.py --source "$SOURCE" --results build/skeleton-results
```

別ディレクトリと空のGradleキャッシュで公開版を解決し、実行・許容・直接呼出し違反・参照違反・修正・依存更新を確認します。
各段階の実終了コードと診断を保存します。意図した違反の `check` が失敗したことを確認する検証スクリプト全体は成功で終わります。
これは段階ごとの検証で、独立したconsumerリポジトリにおける失敗コミット→修正コミットのCI履歴とは区別します。
