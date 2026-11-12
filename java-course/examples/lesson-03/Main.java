public class Main {
  public static void main(String[] args) {
    int n = 173, ones = 0, steps = 0;
    while (n > 0) {
      ones += n % 2;
      n /= 2;
      steps++;
    }
    System.out.println(ones);
    System.out.println(steps);
  }
}
