import java.util.Arrays;
public class Main {
  public static void main(String[] args) {
    int[][] w = {{0,2,4,12},{0,0,1,7},
                 {0,0,0,3},{0,0,0,0}};
    int[] d = {0,999,999,999};
    for (int v = 0; v < 4; v++) {
      if (d[v] == 999) continue;
      for (int u = v + 1; u < 4; u++) {
        if (w[v][u] > 0)
          d[u] = Math.min(d[u],d[v]+w[v][u]);
      }
    }
    System.out.println(Arrays.toString(d));
  }
}
