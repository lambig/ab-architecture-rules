# ab-architecture-rules

ABが採用する設計方針を、実装上の制約として検査するArchUnit規則です。
現在の規則は、指定したメソッドへの直接呼出しとメソッド参照を、許可したクラス内に限定します。

## 採用する設計方針

ABでは、複数の集約に関係する遷移の入口を操作オブジェクトへ集め、呼出元が個別の遷移へ直接入り込む経路を制限します。
このライブラリは、その境界をbytecodeから検査するためのものです。すべてのJavaプロジェクトに必須の設計ではありません。
同じ制約を採用する利用側が、検査対象・許可元・適用規則を明示して使います。

業務上の事前条件や遷移順序は、この検査だけでは保証できません。たとえば許可された操作が不正な順序でメソッドを呼んでも、
アクセス元の制約は満たします。状態や順序の正しさは利用側の試験で検証してください。

ABServiceの業務型・注釈・package・設定には依存しません。
通常の汎用ライブラリをまとめるtoolbox-javaの標準依存にも含めず、採用するプロジェクトが直接テスト依存を宣言します。
依存を追加しただけで検査が自動実行されることはありません。

## 自分のプロジェクトへ導入する

ライブラリと検査実行の最低Javaは8、依存するArchUnitは1.5.0です。公開APIにArchUnitの型が現れるため、POMのcompile依存から解決します。
ライブラリ本体はJUnitに依存しません。以下の例はJUnit 4を利用しますが、別のテスト基盤からも同じ規則を実行できます。
ソースのビルドにはJDK 17以上、固定Gradle wrapper 9.7.1を使います。例のMaven操作はMaven 3.6.3以上を対象とします。

座標は `io.github.lambig:ab-architecture-rules:0.1.0` です。
初回公開が完了するまではMaven Centralから取得できません。その間のソース検証には後述の候補版手順を使ってください。

Gradleでは次のように直接参照します。

```groovy
repositories { mavenCentral() }
dependencies {
    testImplementation 'io.github.lambig:ab-architecture-rules:0.1.0'
    testImplementation 'junit:junit:4.13.2'
}
```

Mavenではtest scopeを指定します。

```xml
<dependency>
  <groupId>io.github.lambig</groupId>
  <artifactId>ab-architecture-rules</artifactId>
  <version>0.1.0</version>
  <scope>test</scope>
</dependency>
```

1. 制限対象と許可元を表す注釈を用意します。[Transition](example/src/main/java/example/shipping/Transition.java)と
   [Operation](example/src/main/java/example/shipping/Operation.java)が例です。注釈をclassファイルに残す必要があります。
2. [BoundaryCheck.java](example/src/test/java/example/shipping/BoundaryCheck.java)の注釈型と `importPackages` を自分の対象に合わせます。
   制限対象と呼出元の両方をimportしてください。規則の `check(JavaClasses)` が検査の実行入口です。
3. Gradleの `check` またはMavenの `verify` をCIから実行します。

注釈以外の条件には `MethodAccessRules.onlyAccessedBy(targets, allowedCallers)` へArchUnitの `DescribedPredicate` を渡します。
公開APIは `io.github.lambig.ab.architecture.MethodAccessRules` です。
引数・null・空選択の契約は[日本語Javadoc](src/main/java/io/github/lambig/ab/architecture/MethodAccessRules.java)を参照してください。
API文書は `sh gradlew javadoc` で `build/docs/javadoc/index.html` へ生成でき、公開物には同じ版のsources/Javadoc JARを含めます。

## 動く例で許容・違反・修正を確認する

[example](example/)は独立したプロジェクトです。GradleとMavenで同じソースを使います。
例を空のディレクトリへコピーしても、ライブラリのソースやcomposite buildに依存せずPOM/JARから解決します。
アプリケーション側のruntime依存は空で、検査用依存はテスト側に限定されます。

リポジトリのルートで実行します。JDK 17以上とMavenをPATHへ設定してください。

```sh
sh verify-example.sh
```

この操作はライブラリの契約試験と候補JAR・POM・sources・Javadocの生成を行い、一時ディレクトリへ例をコピーして検証します。
Mavenのローカルキャッシュも一時ディレクトリに分離します。結果は `build/consumer-results/candidate/` に残ります。

```text
gradle: allowed PASS; direct REJECTED; reference REJECTED; fixed PASS; runtime isolated
maven: allowed PASS; direct REJECTED; reference REJECTED; fixed PASS; runtime isolated
```

| 段階 | ソース | 期待する結果 |
| --- | --- | --- |
| allowed | [操作内の呼出しと参照](example/src/scenarios/allowed/java/example/shipping/DispatchOperation.java) | 両方とも許可される |
| direct | [操作外の直接呼出し](example/src/scenarios/direct/java/example/shipping/Client.java) | ClientからShipment.dispatchへの呼出しで失敗する |
| reference | [操作外のメソッド参照](example/src/scenarios/reference/java/example/shipping/Client.java) | Clientによる参照の取得で失敗する |
| fixed | [修正したClient](example/src/scenarios/fixed/java/example/shipping/Client.java)と[操作](example/src/scenarios/fixed/java/example/shipping/DispatchOperation.java) | 操作を経由することで成功する |

診断には呼出元・対象メソッド・ソース位置と、`expected caller class` に続く許可条件が表示されます。
検証スクリプトはこの診断を照合し、依存解決やコンパイルの失敗を違反検出の成功とは扱いません。
修正例では検査を無効にせず、アクセスを許可された操作へ移します。

一段階ずつ試す場合は、候補を作ってから例をコピーします。

```sh
sh gradlew publishMavenJavaPublicationToCandidateRepository
repository="file:$(pwd)/build/repository"
consumer=$(mktemp -d)
cp -R example/. "$consumer/"
cd "$consumer"
sh gradlew "-ParchitectureRulesRepository=$repository" -Pscenario=allowed clean check
mvn "-DarchitectureRulesRepository=$repository" -Dscenario=allowed clean verify
```

`scenario` を `direct`、`reference`、`fixed` の順に変えて再実行します。前二つは意図的に失敗します。
Windowsでは `gradlew.bat` と `mvn` に同じ引数を渡せます。候補のリポジトリには絶対file URLを指定してください。

CIはJDK 17でビルドし、Java 8で導入例の検査を実行します。手元でも別JVMを指定できます。

```sh
BOUNDARY_JAVA_HOME=/path/to/jdk8 sh verify-example.sh
```

## 検出範囲と限界

- 直接呼出しとメソッド参照の取得を検査します。参照を実行したかどうかは問いません。
- アクセス元コードを所有するクラスを判定します。外側のクラスの注釈で内側のクラスを自動許可しません。
- 注釈方式は直接付与された注釈を照合し、meta-annotationを許可条件にしません。
- 対象メソッドが一件も選ばれなければ、ArchUnit全体の空選択設定に関わらず失敗します。
  選ばれたメソッドにアクセスがないことは許可します。
- 一部の対象への注釈漏れやimport範囲外の呼出元は検出できません。対象一覧とimport範囲は利用側で確認します。
- reflection、動的生成コード、業務順序、transaction、権限や値の妥当性は保証しません。
- 操作内で取得したメソッド参照を外へ返すことは許可します。実行スレッドや実行時刻を操作内に限定する保証はありません。

## 公開版の取得と更新

固定版の公開後は `sh verify-example.sh public` でMaven Centralから取得して同じ一連操作を実行します。
候補リポジトリを指定せず、MavenとGradleの両方に新しいキャッシュを使います。

更新では利用側の依存版を変更し、許容→直接呼出しの違反→参照の違反→修正の検証と、利用側の回帰試験を再実行します。
例では `RULES_VERSION=<公開された固定版> sh verify-example.sh public` を使えます。
互換性の確認箇所は最低Java・ArchUnit版・公開メソッド・注釈の扱い・診断・空選択の契約です。
問題があれば直前に検証済みの固定版へ戻して、同じ検証を実行してください。公開した固定版は上書きしません。

ソースの修正から公開までの手順は[RELEASING.md](RELEASING.md)、不具合・提案は[Issues](https://github.com/lambig/ab-architecture-rules/issues)へ。
ArchUnitのimportと規則の基本は[公式ガイド](https://www.archunit.org/userguide/html/000_Index.html)を参照してください。
