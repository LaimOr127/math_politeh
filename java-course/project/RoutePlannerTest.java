import java.util.List;
public class RoutePlannerTest {
  static void check(boolean condition) { if (!condition) throw new AssertionError(); }
  static void rejects(Runnable action) {
    try { action.run(); } catch (IllegalArgumentException expected) { return; }
    throw new AssertionError("Expected invalid input");
  }
  static int brute(int[][] graph,int at,int end) {
    if (at == end) return 0;
    int result = 1000000;
    for (int next = at+1; next < graph.length; next++)
      if (graph[at][next] > 0) result = Math.min(result,graph[at][next]+brute(graph,next,end));
    return result;
  }
  public static void main(String[] args) {
    check(RoutePlanner.solve(1, false).cost() == 6);
    check(RoutePlanner.solve(1, false).path().equals("A-C-B-D"));
    check(RoutePlanner.solve(2, false).cost() == 7);
    check(RoutePlanner.solve(99, false).cost() == 7);
    check(RoutePlanner.solve(1, true).cost() == 7);
    check(RoutePlanner.plan(new int[][]{{0,0},{0,0}},0,1).cost() == -1);
    check(RoutePlanner.plan(new int[][]{{0}},0,0).vertices().equals(List.of(0)));
    rejects(() -> RoutePlanner.solve(0, false));
    rejects(() -> RoutePlanner.solve(100, false));
    rejects(() -> RoutePlanner.plan(new int[][]{{0,1},{1,0}},0,1));
    rejects(() -> RoutePlanner.plan(new int[][]{{0,-1},{0,0}},0,1));
    rejects(() -> RoutePlanner.plan(new int[][]{{0}},0,1));
    for (String s : new String[]{"0","100","-1","01",""," ","<script>","1&x=2"})
      rejects(() -> RoutePlanner.parseWeight(s));
    check(RoutePlanner.parseWeight("1") == 1);
    check(RoutePlanner.parseWeight("99") == 99);
    var random = new java.util.Random(42);
    for (int trial = 0; trial < 100; trial++) {
      int[][] g = new int[6][6];
      for (int a = 0; a < 6; a++) for (int b = a+1; b < 6; b++)
        if (random.nextBoolean()) g[a][b] = 1+random.nextInt(99);
      int expected = brute(g,0,5);
      check(RoutePlanner.plan(g,0,5).cost() == (expected == 1000000 ? -1 : expected));
    }
    System.out.println("OK");
  }
}
