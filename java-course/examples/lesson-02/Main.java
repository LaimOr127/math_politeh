public class Main {
  public static void main(String[] args) {
    int opened = 0;
    for (int mask = 0; mask < 8; mask++) {
      boolean p = (mask & 4) != 0;
      boolean s = (mask & 2) != 0;
      boolean e = (mask & 1) != 0;
      if ((p && s) || e) opened++;
    }
    System.out.println(opened);
  }
}
