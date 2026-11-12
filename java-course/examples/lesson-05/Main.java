public class Main {
  public static void main(String[] args) {
    String s = "BAAACABAA";
    int cur = 0, best = 0;
    for (int i = 0; i < s.length(); i++) {
      boolean aa = i > 0 && s.charAt(i-1) == 'A'
          && s.charAt(i) == 'A';
      cur = aa ? 1 : cur + 1;
      best = Math.max(best, cur);
    }
    System.out.println(best);
  }
}
