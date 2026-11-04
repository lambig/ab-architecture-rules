package example.shipping;

public final class Client {
    public Runnable deferred(Shipment shipment) {
        return shipment::dispatch;
    }
}
