import { expect, test } from "bun:test";
import { hello } from "../src/index.ts";

test("hello", () => {
	expect(hello("demo")).toBe("Hello, demo!");
});
