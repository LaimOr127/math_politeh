import com.sun.net.httpserver.*;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.io.IOException;

/** Local classroom demonstration. No uploaded code, files or arbitrary URLs. */
public class Main {
  static final String HTML = """
    <!doctype html><html lang="ru"><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Маршрутный центр</title><link rel="stylesheet" href="/style.css">
    <script src="/app.js" defer></script><main>
    <p>Орбита Java / итоговый проект</p><h1>Маршрутный центр</h1>
    <p>Найдите минимальное время от A до D по направленным линиям.</p>
    <pre>A → C: 2   A → B: 4   A → D: 12
    C → B: w   C → D: 7   B → D: 3</pre>
    <form action="/route" method="get"><label for="w">Цена C → B, 1–99</label>
    <input id="w" name="w" type="number" min="1" max="99" value="1" required>
    <button>Рассчитать маршрут</button></form>
    <p id="result" role="status">Измените цену и сравните маршруты.</p>
    <p>При w = 2 существуют два оптимальных пути. Сможете найти оба?</p></main></html>
    """;
  static final String CSS = """
    :root{color-scheme:dark}body{background:#101c2b;color:#eaf1f5;font:18px/1.6 Arial;margin:0}
    main{max-width:760px;margin:60px auto;padding:24px}h1{font-size:42px}pre{overflow:auto}
    label{display:block}input,button{font:inherit;padding:12px;margin:10px 8px 10px 0}
    button{background:#9eeaf0;color:#101c2b;border:0;border-radius:6px;cursor:pointer}
    :focus-visible{outline:3px solid #ffc58b;outline-offset:4px}#result{color:#ffc58b}
    @media(max-width:600px){main{margin:15px auto}h1{font-size:32px}}
    """;
  static final String JS = """
    document.querySelector('form').addEventListener('submit',async event=>{
      event.preventDefault();const output=document.querySelector('#result');
      try{const value=document.querySelector('#w').value;
        const r=await fetch('/route?w='+encodeURIComponent(value));
        if(!r.ok)throw Error('Проверьте цену: целое число от 1 до 99.');
        const data=await r.json();output.textContent=data.cost+' минут: '+data.path;
      }catch(e){output.textContent=e.message||'Сервер недоступен';}
    });
    """;
  static void send(HttpExchange exchange,int status,String type,String text) throws IOException {
    byte[] bytes = text.getBytes(StandardCharsets.UTF_8);
    exchange.getResponseHeaders().set("Content-Type",type+"; charset=utf-8");
    exchange.getResponseHeaders().set("X-Content-Type-Options","nosniff");
    exchange.getResponseHeaders().set("Cache-Control","no-store");
    exchange.getResponseHeaders().set("Content-Security-Policy",
      "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'");
    exchange.sendResponseHeaders(status,bytes.length);
    exchange.getResponseBody().write(bytes);
  }
  static void handle(HttpExchange exchange) throws IOException {
    try(exchange) {
      if(!exchange.getRequestMethod().equals("GET")) {
        exchange.getResponseHeaders().set("Allow","GET");
        send(exchange,405,"text/plain","Method not allowed"); return;
      }
      String path=exchange.getRequestURI().getRawPath();
      switch(path) {
        case "/" -> send(exchange,200,"text/html",HTML);
        case "/style.css" -> send(exchange,200,"text/css",CSS);
        case "/app.js" -> send(exchange,200,"text/javascript",JS);
        case "/route" -> {
          String query=exchange.getRequestURI().getRawQuery();
          if(query==null || !query.matches("w=[1-9][0-9]?")) {
            send(exchange,400,"text/plain","Expected exactly w=1..99"); return;
          }
          int w=RoutePlanner.parseWeight(query.substring(2));
          var route=RoutePlanner.solve(w,false);
          send(exchange,200,"application/json","{\"cost\":"+route.cost()+",\"path\":\""+route.path()+"\"}");
        }
        default -> send(exchange,404,"text/plain","Not found");
      }
    }
  }
  public static void main(String[] args) throws IOException {
    var server=HttpServer.create(new InetSocketAddress("127.0.0.1",8090),16);
    server.createContext("/",Main::handle);
    server.start();
    System.out.println("http://127.0.0.1:8090");
  }
}
