import java.util.Scanner;
public class ReadInput {
  public static void main(String[] args) {
    var input = new Scanner(System.in);
    if (!input.hasNextInt()) {
      System.out.println("invalid"); return;
    }
    int energy = input.nextInt();
    if (!input.hasNextInt()) {
      System.out.println("invalid"); return;
    }
    int cost = input.nextInt();
    if (energy < 0 || cost <= 0) {
      System.out.println("invalid"); return;
    }
    System.out.println(energy / cost);
    System.out.println(energy % cost);
  }
}
