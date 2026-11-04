package example.shipping;

public final class Client {
    private final DispatchOperation operation = new DispatchOperation();

    public void dispatch(Shipment shipment) {
        operation.dispatch(shipment);
    }

    public Runnable deferred(Shipment shipment) {
        return operation.deferred(shipment);
    }
}
