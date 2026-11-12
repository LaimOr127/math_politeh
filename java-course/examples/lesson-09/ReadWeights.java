import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.io.IOException;
public class ReadWeights {
  public static void main(String[] args) {
    Path file = Path.of("weights.txt");
    try {
      if (Files.size(file) > 100)
        throw new IllegalArgumentException();
      var lines = Files.readAllLines(file, StandardCharsets.UTF_8);
      if (lines.size() != 1 ||
          !lines.get(0).matches("[1-9][0-9]?"))
        throw new IllegalArgumentException();
      System.out.println(Integer.parseInt(lines.get(0)));
    } catch (IOException | IllegalArgumentException e) {
      System.out.println("invalid");
    }
  }
}
