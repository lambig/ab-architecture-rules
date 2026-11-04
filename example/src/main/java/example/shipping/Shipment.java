package example.shipping;

public final class Shipment {
    @Transition
    public void dispatch() {
        // 検査境界を示す例。業務上の不変条件は利用側が所有する。
    }
}
