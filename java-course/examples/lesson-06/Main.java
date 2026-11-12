public class Main {
  public static void main(String[] args) {
    int n = 6;
    long[] dp = new long[n + 1];
    dp[0] = 1;
    for (int i = 1; i <= n; i++) {
      dp[i] = dp[i - 1];
      if (i >= 2) dp[i] += dp[i - 2];
    }
    System.out.println(dp[n]);
  }
}
