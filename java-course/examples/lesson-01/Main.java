public class Main {
  public static void main(String[] args) {
    int energy = 95;
    int cost = 12;
    int sessions = energy / cost;
    int rest = energy % cost;
    System.out.println(sessions);
    System.out.println(rest);
    System.out.println(1L * 50000 * 50000);
  }
}
