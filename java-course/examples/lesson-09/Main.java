public class Main {
  static int parseWeight(String s) {
    if (!s.matches("[1-9][0-9]?"))
      throw new IllegalArgumentException("1..99");
    return Integer.parseInt(s);
  }
  public static void main(String[] args) {
    System.out.println(parseWeight("12"));
    try { parseWeight("-5"); }
    catch (IllegalArgumentException e) {
      System.out.println("invalid");
    }
  }
}
