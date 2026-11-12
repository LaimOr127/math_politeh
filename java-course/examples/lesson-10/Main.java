import java.net.URI;
import java.net.http.*;
public class Main {
  public static void main(String[] args) throws Exception {
    var client = HttpClient.newHttpClient();
    var request = HttpRequest.newBuilder(
        URI.create("http://127.0.0.1:8090/route?w=1"))
        .GET().build();
    var response = client.send(request,
        HttpResponse.BodyHandlers.ofString());
    System.out.println(response.statusCode());
    System.out.println(response.body());
  }
}
