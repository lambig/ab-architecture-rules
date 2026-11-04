package io.github.lambig.ab.architecture;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;

import com.tngtech.archunit.ArchConfiguration;
import com.tngtech.archunit.base.DescribedPredicate;
import com.tngtech.archunit.core.domain.JavaClass;
import com.tngtech.archunit.core.domain.JavaMethod;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import org.junit.Test;

public class MethodAccessRulesTest {
    private static final DescribedPredicate<JavaMethod> RESTRICTED =
            DescribedPredicate.describe("named restricted", method -> method.getName().equals("restricted"));
    private static final DescribedPredicate<JavaClass> CALLER =
            DescribedPredicate.describe("named Caller", type -> type.getSimpleName().equals("Caller"));

    @Test
    public void acceptsConsumerPredicatesWithoutAnnotations() {
        assertFalse(MethodAccessRules.onlyAccessedBy(RESTRICTED, CALLER)
                .evaluate(new ClassFileImporter().importClasses(Target.class, Caller.class)).hasViolation());
    }

    @Test
    public void rejectsCallerOutsideConsumerPredicateWithUsefulDiagnostic() {
        String message = MethodAccessRules.onlyAccessedBy(RESTRICTED, CALLER)
                .evaluate(new ClassFileImporter().importClasses(Target.class, Outsider.class))
                .getFailureReport().toString();
        assertTrue(message.contains("Outsider"));
        assertTrue(message.contains("restricted"));
        assertTrue(message.contains("expected caller class named Caller"));
    }

    @Test
    public void failsEmptySelectionEvenWhenGlobalDefaultAllowsIt() {
        ArchConfiguration.withThreadLocalScope(configuration -> {
            configuration.setProperty("archRule.failOnEmptyShould", "false");
            assertThrows(AssertionError.class, () -> MethodAccessRules.onlyAccessedBy(RESTRICTED, CALLER)
                    .check(new ClassFileImporter().importClasses(Caller.class)));
        });
    }

    @Test
    public void rejectsNullPolicyInsteadOfSilentlySkippingChecks() {
        assertThrows(NullPointerException.class, () -> MethodAccessRules.onlyAccessedBy(null, CALLER));
        assertThrows(NullPointerException.class, () -> MethodAccessRules.onlyAccessedBy(RESTRICTED, null));
        assertThrows(NullPointerException.class, () ->
                MethodAccessRules.annotatedMethodsOnlyAccessedByAnnotatedClasses(null, Deprecated.class));
        assertThrows(NullPointerException.class, () ->
                MethodAccessRules.annotatedMethodsOnlyAccessedByAnnotatedClasses(Deprecated.class, null));
    }

    static class Target { void restricted() { } }
    static class Caller { void call(Target target) { target.restricted(); } }
    static class Outsider { void call(Target target) { target.restricted(); } }
}
