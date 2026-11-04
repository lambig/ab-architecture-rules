package example.shipping;

@Operation
public final class DispatchOperation {
    public void dispatch(Shipment shipment) {
        shipment.dispatch();
    }

    public Runnable deferred(Shipment shipment) {
        return shipment::dispatch;
    }
}
