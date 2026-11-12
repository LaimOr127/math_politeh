public class Main {
  public static void main(String[] args) {
    int[] a = {2, 8, 2, 8, 5, 5};
    int[] seen = new int[11];
    long pairs = 0;
    for (int x : a) {
      pairs += seen[10 - x];
      seen[x]++;
    }
    System.out.println(pairs);
  }
}
