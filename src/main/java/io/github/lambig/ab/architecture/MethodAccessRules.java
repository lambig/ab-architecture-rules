package io.github.lambig.ab.architecture;

import static com.tngtech.archunit.core.domain.properties.CanBeAnnotated.Predicates.annotatedWith;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.methods;

import com.tngtech.archunit.base.DescribedPredicate;
import com.tngtech.archunit.core.domain.JavaClass;
import com.tngtech.archunit.core.domain.JavaMethod;
import com.tngtech.archunit.lang.ArchCondition;
import com.tngtech.archunit.lang.ArchRule;
import com.tngtech.archunit.lang.ConditionEvents;
import com.tngtech.archunit.lang.SimpleConditionEvent;
import java.lang.annotation.Annotation;
import java.util.Objects;

/**
 * ABの設計方針として、指定したメソッドへのアクセスを許可したクラス内に限定する規則。
 *
 * <p>制約を採用する利用側が明示的に実行する。汎用的なJava設計の正解を定義するものではなく、
 * ABService固有の型やpackageにも依存しない。
 *
 * <p>利用側が業務上の制約を指定し、対象メソッドと呼出元の両方のクラスをimportする。
 * このbytecode検査は、業務上の実行順序を保証せず、reflectionによるアクセスも検出しない。
 */
public final class MethodAccessRules {
    private MethodAccessRules() {
    }

    /**
     * 指定したメソッドへのアクセスを、許可条件に一致する呼出元クラスに限定する。
     *
     * <p>直接呼出しとメソッド参照の両方を検査する。呼出元クラスはアクセス元のコードを
     * 所有するクラスであり、外側のクラスが許可されていても内側のクラスは自動的には許可されない。
     * ArchUnit全体の空選択に対する失敗設定を無効にしていても、対象メソッドが一件もなければ失敗する。
     * importした対象メソッドにアクセスが一件もない場合は許可する。
     *
     * @param targets アクセスを検査する対象メソッドの選択条件
     * @param allowedCallers アクセス元のコードを所有するクラスの許可条件
     * @return 利用側がimportしたクラスに適用するArchUnit規則
     * @throws NullPointerException いずれかの条件がnullの場合
     */
    public static ArchRule onlyAccessedBy(
            DescribedPredicate<? super JavaMethod> targets,
            DescribedPredicate<? super JavaClass> allowedCallers) {
        Objects.requireNonNull(targets, "targets");
        Objects.requireNonNull(allowedCallers, "allowedCallers");
        return methods().that(targets)
                .should(new ArchCondition<JavaMethod>("only be accessed by classes " + allowedCallers.getDescription()) {
                    @Override
                    public void check(JavaMethod method, ConditionEvents events) {
                        // onlyBeCalled()では対象外となるFoo::methodの参照も含める。
                        method.getAccessesToSelf().forEach(access -> {
                            if (!allowedCallers.test(access.getOriginOwner())) {
                                events.add(SimpleConditionEvent.violated(access,
                                        access.getDescription() + "; expected caller class "
                                                + allowedCallers.getDescription()));
                            }
                        });
                    }
                })
                .allowEmptyShould(false);
    }

    /**
     * 利用側が定義した注釈で、対象メソッドと許可する呼出元クラスを選択する。
     *
     * <p>注釈はclassファイルに保持される必要がある。ArchUnitの
     * {@code annotatedWith}条件で直接付与された注釈を照合するため、meta-annotationや
     * 外側のクラスの注釈によって許可されることはない。import範囲の要件と
     * 対象メソッドが一件もない場合の扱いは、{@link #onlyAccessedBy}を参照。
     *
     * @param targetAnnotation アクセスを制限するメソッドに付与する注釈型
     * @param callerAnnotation 許可する呼出元クラスに付与する注釈型
     * @return 指定した注釈で構成したアクセス規則
     * @throws NullPointerException いずれかの注釈型がnullの場合
     */
    public static ArchRule annotatedMethodsOnlyAccessedByAnnotatedClasses(
            Class<? extends Annotation> targetAnnotation,
            Class<? extends Annotation> callerAnnotation) {
        Objects.requireNonNull(targetAnnotation, "targetAnnotation");
        Objects.requireNonNull(callerAnnotation, "callerAnnotation");
        return onlyAccessedBy(annotatedWith(targetAnnotation), annotatedWith(callerAnnotation));
    }
}
