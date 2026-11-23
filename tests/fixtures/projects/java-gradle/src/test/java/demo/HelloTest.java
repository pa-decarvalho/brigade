package demo;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class HelloTest {
    @Test
    void hello() {
        assertEquals("Hello from demo!", Hello.hello());
    }
}
