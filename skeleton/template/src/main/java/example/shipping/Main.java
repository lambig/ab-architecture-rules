package example.shipping;

import io.github.lambig.textescape.TextEscape;

public final class Main {
    public static void main(String[] args) {
        new DispatchOperation().dispatch(new Shipment());
        String message = TextEscape.escape("${operation}: ${status}")
                .where("operation", "dispatch").where("status", "ready").compile();
        if (!"dispatch: ready".equals(message)) throw new AssertionError(message);
        System.out.println(message);
    }
}
