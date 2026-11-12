import java.util.*;

/** Directed acyclic graphs with ascending vertex indices and weights 1..99. */
public class RoutePlanner {
  public record Result(int cost, List<Integer> vertices) {
    public Result { vertices = List.copyOf(vertices); }
  }
  public record Route(int cost, String path) {}

  /** Parses an exact decimal weight. Does not normalize malformed input. */
  public static int parseWeight(String value) {
    if (value == null || !value.matches("[1-9][0-9]?"))
      throw new IllegalArgumentException("Weight must be 1..99");
    return Integer.parseInt(value);
  }

  /** Pure fixed-map use case; w is the price of C to B. */
  public static Route solve(int w, boolean closed) {
    if (w < 1 || w > 99) throw new IllegalArgumentException("Weight must be 1..99");
    int[][] graph = {{0,2,4,12},{0,0,closed ? 0 : w,7},
                     {0,0,0,3},{0,0,0,0}};
    Result result = plan(graph,0,3);
    String[] names = {"A","C","B","D"};
    var labels = new ArrayList<String>();
    for (int vertex : result.vertices()) labels.add(names[vertex]);
    return new Route(result.cost(), String.join("-",labels));
  }

  /** Returns one minimum path; -1 and empty vertices denote no route.
   * Matrix rows and columns are a declared topological order. Zero means no edge.
   * Input is read only. Size bound makes all finite costs smaller than INF. */
  public static Result plan(int[][] graph, int start, int end) {
    if (graph == null || graph.length == 0 || graph.length > 50)
      throw new IllegalArgumentException("Graph size must be 1..50");
    int n = graph.length;
    if (start < 0 || start >= n || end < 0 || end >= n)
      throw new IllegalArgumentException("Unknown vertex");
    for (int v = 0; v < n; v++) {
      if (graph[v] == null || graph[v].length != n)
        throw new IllegalArgumentException("Square matrix required");
      for (int u = 0; u < n; u++)
        if (graph[v][u] < 0 || graph[v][u] > 99 || (u <= v && graph[v][u] != 0))
          throw new IllegalArgumentException("Ascending DAG with weights 1..99 required");
    }
    final int INF = 1000000;
    int[] distance = new int[n], parent = new int[n];
    Arrays.fill(distance,INF); Arrays.fill(parent,-1); distance[start] = 0;
    for (int v = 0; v < n; v++) {
      if (distance[v] == INF) continue;
      for (int u = v + 1; u < n; u++) {
        if (graph[v][u] == 0) continue;
        int candidate = distance[v] + graph[v][u];
        if (candidate < distance[u]) { distance[u] = candidate; parent[u] = v; }
      }
    }
    if (distance[end] == INF) return new Result(-1,List.of());
    var route = new ArrayList<Integer>();
    for (int at = end; at != -1; at = parent[at]) route.add(at);
    Collections.reverse(route);
    return new Result(distance[end],route);
  }
}
