import java.util.*;
public class Main {
  public static void main(String[] args) {
    int[][] g = {{1,2},{3},{1,3},{}};
    int[] d = {-1,-1,-1,-1};
    ArrayDeque<Integer> q = new ArrayDeque<>();
    d[0] = 0; q.add(0);
    while (!q.isEmpty()) {
      int v = q.remove();
      for (int u : g[v]) if (d[u] == -1) {
        d[u] = d[v] + 1; q.add(u);
      }
    }
    System.out.println(d[3]);
  }
}
