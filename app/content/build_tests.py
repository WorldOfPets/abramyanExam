"""Build the task catalogue and hidden autotests.

The reference solutions live only in this development script. The generated
``tasks.json`` contains statements, samples and expected outputs, so the exam
binary can grade submissions without shipping the solutions.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from pathlib import Path

OUT = Path(__file__).with_name("tasks.json")

BLOCKS = {
    "integer": "Целые числа",
    "if": "Условный оператор",
    "for": "Цикл с параметром",
    "proc": "Процедуры и функции",
    "series": "Последовательности",
}


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return str(value)
        if value == 0:
            return "0"
        return f"{value:.12g}"
    return str(value)


def lines(values: list[object] | tuple[object, ...]) -> str:
    return "\n".join(fmt(v) for v in values)


def joined(values: list[object] | tuple[object, ...]) -> str:
    return " ".join(fmt(v) for v in values)


def as_ints(raw: str) -> list[int]:
    return [int(x) for x in raw.split()]


def as_floats(raw: str) -> list[float]:
    return [float(x) for x in raw.split()]


def sign(x: float) -> int:
    return -1 if x < 0 else (1 if x > 0 else 0)


def digits(n: int) -> list[int]:
    return [int(ch) for ch in str(n)]


def reverse_int(n: int) -> int:
    return int(str(n)[::-1])


def is_sorted_asc(values: list[float]) -> bool:
    return all(values[i] <= values[i + 1] for i in range(len(values) - 1))


def is_sorted_desc(values: list[float]) -> bool:
    return all(values[i] >= values[i + 1] for i in range(len(values) - 1))


def count_roots(a: float, b: float, c: float) -> int:
    d = b * b - 4 * a * c
    if d > 1e-12:
        return 2
    if abs(d) <= 1e-12:
        return 1
    return 0


def solve_integer_1(raw: str) -> str:
    return str(as_ints(raw)[0] // 100)


def solve_integer_2(raw: str) -> str:
    return str(as_ints(raw)[0] // 1000)


def solve_integer_3(raw: str) -> str:
    return str(as_ints(raw)[0] // 1024)


def solve_integer_4(raw: str) -> str:
    a, b = as_ints(raw)[:2]
    return str(a // b)


def solve_integer_5(raw: str) -> str:
    a, b = as_ints(raw)[:2]
    return str(a % b)


def solve_integer_6(raw: str) -> str:
    n = as_ints(raw)[0]
    return lines([n // 10, n % 10])


def solve_integer_7(raw: str) -> str:
    a, b = digits(as_ints(raw)[0])
    return lines([a + b, a * b])


def solve_integer_8(raw: str) -> str:
    n = as_ints(raw)[0]
    return str((n % 10) * 10 + n // 10)


def solve_integer_9(raw: str) -> str:
    return str(as_ints(raw)[0] // 100)


def solve_integer_10(raw: str) -> str:
    n = as_ints(raw)[0]
    return lines([n % 10, (n // 10) % 10])


def solve_integer_11(raw: str) -> str:
    a, b, c = digits(as_ints(raw)[0])
    return lines([a + b + c, a * b * c])


def solve_integer_12(raw: str) -> str:
    return str(reverse_int(as_ints(raw)[0]))


def solve_integer_13(raw: str) -> str:
    n = as_ints(raw)[0]
    return str((n % 100) * 10 + n // 100)


def solve_integer_14(raw: str) -> str:
    n = as_ints(raw)[0]
    return str((n % 10) * 100 + n // 10)


def solve_integer_15(raw: str) -> str:
    n = as_ints(raw)[0]
    h, t, o = n // 100, (n // 10) % 10, n % 10
    return str(t * 100 + h * 10 + o)


def solve_integer_16(raw: str) -> str:
    n = as_ints(raw)[0]
    h, t, o = n // 100, (n // 10) % 10, n % 10
    return str(h * 100 + o * 10 + t)


def solve_integer_17(raw: str) -> str:
    return str((as_ints(raw)[0] // 100) % 10)


def solve_integer_18(raw: str) -> str:
    return str((as_ints(raw)[0] // 1000) % 10)


def solve_integer_19(raw: str) -> str:
    return str(as_ints(raw)[0] // 60)


def solve_integer_20(raw: str) -> str:
    return str(as_ints(raw)[0] // 3600)


def solve_if_1(raw: str) -> str:
    n = as_ints(raw)[0]
    return str(n + 1 if n > 0 else n)


def solve_if_2(raw: str) -> str:
    n = as_ints(raw)[0]
    return str(n + 1 if n > 0 else n - 2)


def solve_if_3(raw: str) -> str:
    n = as_ints(raw)[0]
    return str(n + 1 if n > 0 else (n - 2 if n < 0 else 10))


def solve_if_4(raw: str) -> str:
    return str(sum(1 for x in as_ints(raw) if x > 0))


def solve_if_5(raw: str) -> str:
    values = as_ints(raw)
    return lines([sum(1 for x in values if x > 0), sum(1 for x in values if x < 0)])


def solve_if_6(raw: str) -> str:
    return str(max(as_ints(raw)))


def solve_if_7(raw: str) -> str:
    a, b = as_ints(raw)[:2]
    return str(1 if a <= b else 2)


def solve_if_8(raw: str) -> str:
    values = as_ints(raw)[:2]
    return lines(sorted(values, reverse=True))


def solve_if_9(raw: str) -> str:
    values = as_floats(raw)[:2]
    return lines(sorted(values))


def solve_if_10(raw: str) -> str:
    a, b = as_ints(raw)[:2]
    if a != b:
        a = b = a + b
    else:
        a = b = 0
    return lines([a, b])


def solve_if_11(raw: str) -> str:
    a, b = as_ints(raw)[:2]
    if a != b:
        a = b = max(a, b)
    else:
        a = b = 0
    return lines([a, b])


def solve_if_12(raw: str) -> str:
    return str(min(as_ints(raw)))


def solve_if_13(raw: str) -> str:
    values = sorted(as_ints(raw))
    return str(values[1])


def solve_if_14(raw: str) -> str:
    values = as_ints(raw)
    return lines([min(values), max(values)])


def solve_if_15(raw: str) -> str:
    values = sorted(as_ints(raw))
    return str(values[-1] + values[-2])


def solve_if_16(raw: str) -> str:
    a, b, c = as_floats(raw)[:3]
    if a < b < c:
        result = [a * 2, b * 2, c * 2]
    else:
        result = [-a, -b, -c]
    return lines(result)


def solve_if_17(raw: str) -> str:
    values = as_floats(raw)[:3]
    if is_sorted_asc(values) or is_sorted_desc(values):
        result = [x * 2 for x in values]
    else:
        result = [-x for x in values]
    return lines(result)


def solve_if_18(raw: str) -> str:
    values = as_ints(raw)[:3]
    for i, value in enumerate(values):
        if values.count(value) == 1:
            return str(i + 1)
    return "1"


def solve_if_19(raw: str) -> str:
    values = as_ints(raw)[:4]
    for i, value in enumerate(values):
        if values.count(value) == 1:
            return str(i + 1)
    return "1"


def solve_if_20(raw: str) -> str:
    a, b, c = as_floats(raw)[:3]
    db, dc = abs(b - a), abs(c - a)
    point, distance = (b, db) if db <= dc else (c, dc)
    return lines([point, distance])


def solve_for_1(raw: str) -> str:
    k, n = as_ints(raw)[:2]
    return joined([k] * n)


def solve_for_2(raw: str) -> str:
    a, b = as_ints(raw)[:2]
    values = list(range(a, b + 1))
    return joined(values + [len(values)])


def solve_for_3(raw: str) -> str:
    a, b = as_ints(raw)[:2]
    values = list(range(b - 1, a, -1))
    if not values:
        return "0"
    return joined(values + [len(values)])


def solve_for_4(raw: str) -> str:
    price = as_floats(raw)[0]
    return lines([price * i for i in range(1, 11)])


def solve_for_5(raw: str) -> str:
    price = as_floats(raw)[0]
    return lines([price * i / 10 for i in range(1, 11)])


def solve_for_6(raw: str) -> str:
    price = as_floats(raw)[0]
    return lines([price * (12 + 2 * i) / 10 for i in range(5)])


def solve_for_7(raw: str) -> str:
    a, b = as_ints(raw)[:2]
    return str(sum(range(a, b + 1)))


def solve_for_8(raw: str) -> str:
    a, b = as_ints(raw)[:2]
    result = 1
    for x in range(a, b + 1):
        result *= x
    return str(result)


def solve_for_9(raw: str) -> str:
    a, b = as_ints(raw)[:2]
    return str(sum(x * x for x in range(a, b + 1)))


def solve_for_10(raw: str) -> str:
    n = as_ints(raw)[0]
    return fmt(sum(1 / i for i in range(1, n + 1)))


def solve_for_11(raw: str) -> str:
    n = as_ints(raw)[0]
    return str(sum(x * x for x in range(n, 2 * n + 1)))


def solve_for_12(raw: str) -> str:
    n = as_ints(raw)[0]
    result = 1.0
    for i in range(1, n + 1):
        result *= 1 + i / 10
    return fmt(result)


def solve_for_13(raw: str) -> str:
    n = as_ints(raw)[0]
    result = 0.0
    for i in range(1, n + 1):
        term = 1 + i / 10
        result += term if i % 2 == 1 else -term
    return fmt(result)


def solve_for_14(raw: str) -> str:
    n = as_ints(raw)[0]
    total = 0
    values = []
    for i in range(1, n + 1):
        total += 2 * i - 1
        values.append(total)
    return lines(values)


def solve_for_15(raw: str) -> str:
    a, n = as_floats(raw)[:2]
    result = 1.0
    for _ in range(int(n)):
        result *= a
    return fmt(result)


def solve_for_16(raw: str) -> str:
    a, n = as_floats(raw)[:2]
    return lines([a**i for i in range(1, int(n) + 1)])


def solve_for_17(raw: str) -> str:
    a, n = as_floats(raw)[:2]
    return fmt(sum(a**i for i in range(int(n) + 1)))


def solve_for_18(raw: str) -> str:
    a, n = as_floats(raw)[:2]
    total = 0.0
    sign_value = 1
    power = 1.0
    for _ in range(int(n) + 1):
        total += sign_value * power
        sign_value = -sign_value
        power *= a
    return fmt(total)


def solve_for_19(raw: str) -> str:
    n = as_ints(raw)[0]
    return fmt(float(math.factorial(n)))


def solve_for_20(raw: str) -> str:
    n = as_ints(raw)[0]
    return fmt(float(sum(math.factorial(i) for i in range(1, n + 1))))


def _proc_lines(raw: str) -> list[float]:
    return as_floats(raw)


def solve_proc_1(raw: str) -> str:
    return lines([x**3 for x in _proc_lines(raw)[:5]])


def solve_proc_2(raw: str) -> str:
    result = []
    for x in _proc_lines(raw)[:5]:
        result.extend([x**2, x**3, x**4])
    return lines(result)


def solve_proc_3(raw: str) -> str:
    a, b, c, d = _proc_lines(raw)[:4]
    result = []
    for x, y in ((a, b), (a, c), (a, d)):
        result.extend([(x + y) / 2, math.sqrt(x * y)])
    return lines(result)


def solve_proc_4(raw: str) -> str:
    result = []
    for a in _proc_lines(raw)[:3]:
        result.extend([3 * a, a * a * math.sqrt(3) / 4])
    return lines(result)


def solve_proc_5(raw: str) -> str:
    values = _proc_lines(raw)[:12]
    result = []
    for i in range(0, 12, 4):
        x1, y1, x2, y2 = values[i : i + 4]
        width, height = abs(x2 - x1), abs(y2 - y1)
        result.extend([2 * (width + height), width * height])
    return lines(result)


def solve_proc_6(raw: str) -> str:
    result = []
    for n in as_ints(raw)[:5]:
        ds = digits(n)
        result.extend([len(ds), sum(ds)])
    return lines(result)


def solve_proc_7(raw: str) -> str:
    return lines([reverse_int(n) for n in as_ints(raw)[:5]])


def solve_proc_8(raw: str) -> str:
    k, d1, d2 = as_ints(raw)[:3]
    first = k * 10 + d1
    second = first * 10 + d2
    return lines([first, second])


def solve_proc_9(raw: str) -> str:
    k, d1, d2 = as_ints(raw)[:3]
    first = int(f"{d1}{k}")
    second = int(f"{d2}{first}")
    return lines([first, second])


def solve_proc_10(raw: str) -> str:
    a, b, c, d = as_floats(raw)[:4]
    a, b = b, a
    c, d = d, c
    b, c = c, b
    return lines([a, b, c, d])


def solve_proc_11(raw: str) -> str:
    values = as_floats(raw)[:4]
    return lines([min(values), max(values)])


def solve_proc_12(raw: str) -> str:
    values = as_floats(raw)[:6]
    return lines(sorted(values[:3]) + sorted(values[3:]))


def solve_proc_13(raw: str) -> str:
    values = as_floats(raw)[:6]
    return lines(sorted(values[:3], reverse=True) + sorted(values[3:], reverse=True))


def solve_proc_14(raw: str) -> str:
    values = as_floats(raw)[:6]
    result = []
    for i in range(0, 6, 3):
        a, b, c = values[i : i + 3]
        result.extend([c, a, b])
    return lines(result)


def solve_proc_15(raw: str) -> str:
    values = as_floats(raw)[:6]
    result = []
    for i in range(0, 6, 3):
        a, b, c = values[i : i + 3]
        result.extend([b, c, a])
    return lines(result)


def solve_proc_16(raw: str) -> str:
    a, b = as_floats(raw)[:2]
    return str(sign(a) + sign(b))


def solve_proc_17(raw: str) -> str:
    values = as_floats(raw)[:9]
    result = []
    for i in range(0, 9, 3):
        result.append(count_roots(*values[i : i + 3]))
    return lines(result)


def solve_proc_18(raw: str) -> str:
    return lines([3.14 * r * r for r in as_floats(raw)[:3]])


def solve_proc_19(raw: str) -> str:
    values = as_floats(raw)[:6]
    return lines([3.14 * (values[i] ** 2 - values[i + 1] ** 2) for i in range(0, 6, 2)])


def solve_proc_20(raw: str) -> str:
    values = as_floats(raw)[:6]
    result = []
    for i in range(0, 6, 2):
        a, h = values[i : i + 2]
        side = math.sqrt((a / 2) ** 2 + h * h)
        result.append(a + 2 * side)
    return lines(result)


def solve_series_1(raw: str) -> str:
    return fmt(sum(as_floats(raw)[:10]))


def solve_series_2(raw: str) -> str:
    result = 1.0
    for x in as_floats(raw)[:10]:
        result *= x
    return fmt(result)


def solve_series_3(raw: str) -> str:
    values = as_floats(raw)[:10]
    return fmt(sum(values) / len(values))


def solve_series_4(raw: str) -> str:
    values = as_floats(raw)
    n = int(values[0])
    data = values[1 : n + 1]
    result = 1.0
    for x in data:
        result *= x
    return lines([sum(data), result])


def solve_series_5(raw: str) -> str:
    values = as_floats(raw)
    n = int(values[0])
    data = values[1 : n + 1]
    parts = [math.floor(x) for x in data]
    return lines([*parts, sum(parts)])


def solve_series_6(raw: str) -> str:
    values = as_floats(raw)
    n = int(values[0])
    data = values[1 : n + 1]
    parts = [x - math.floor(x) for x in data]
    result = 1.0
    for x in parts:
        result *= x
    return lines([*parts, result])


def solve_series_7(raw: str) -> str:
    values = as_floats(raw)
    n = int(values[0])
    data = values[1 : n + 1]
    rounded = [round(x) for x in data]
    return lines([*rounded, sum(rounded)])


def solve_series_8(raw: str) -> str:
    values = as_ints(raw)
    n = values[0]
    data = values[1 : n + 1]
    evens = [x for x in data if x % 2 == 0]
    return lines([*evens, len(evens)])


def solve_series_9(raw: str) -> str:
    values = as_ints(raw)
    n = values[0]
    data = values[1 : n + 1]
    positions = [i + 1 for i, x in enumerate(data) if x % 2 != 0]
    return lines([*positions, len(positions)])


def solve_series_10(raw: str) -> str:
    values = as_ints(raw)
    n = values[0]
    return str(any(x > 0 for x in values[1 : n + 1]))


def solve_series_11(raw: str) -> str:
    values = as_ints(raw)
    k, n = values[0], values[1]
    return str(any(x < k for x in values[2 : 2 + n]))


def _sentinel(raw: str) -> list[int]:
    values = as_ints(raw)
    result = []
    for x in values:
        if x == 0:
            break
        result.append(x)
    return result


def solve_series_12(raw: str) -> str:
    return str(len(_sentinel(raw)))


def solve_series_13(raw: str) -> str:
    return str(sum(x for x in _sentinel(raw) if x > 0 and x % 2 == 0))


def solve_series_14(raw: str) -> str:
    values = as_ints(raw)
    k = values[0]
    return str(sum(1 for x in _sentinel(" ".join(map(str, values[1:]))) if x < k))


def solve_series_15(raw: str) -> str:
    values = as_ints(raw)
    k = values[0]
    data = _sentinel(" ".join(map(str, values[1:])))
    for i, x in enumerate(data):
        if x > k:
            return str(i + 1)
    return "0"


def solve_series_16(raw: str) -> str:
    values = as_ints(raw)
    k = values[0]
    data = _sentinel(" ".join(map(str, values[1:])))
    for i in range(len(data) - 1, -1, -1):
        if data[i] > k:
            return str(i + 1)
    return "0"


def solve_series_17(raw: str) -> str:
    values = as_floats(raw)
    b = values[0]
    n = int(values[1])
    data = values[2 : 2 + n]
    data.append(b)
    data.sort()
    return joined(data)


def solve_series_18(raw: str) -> str:
    values = as_ints(raw)
    n = values[0]
    data = values[1 : n + 1]
    result: list[int] = []
    for x in data:
        if not result or result[-1] != x:
            result.append(x)
    return joined(result)


def solve_series_19(raw: str) -> str:
    values = as_ints(raw)
    n = values[0]
    data = values[1 : n + 1]
    selected = [data[i] for i in range(1, n) if data[i] < data[i - 1]]
    return lines([*selected, len(selected)])


def solve_series_20(raw: str) -> str:
    values = as_ints(raw)
    n = values[0]
    data = values[1 : n + 1]
    selected = [data[i] for i in range(n - 1) if data[i] < data[i + 1]]
    return lines([*selected, len(selected)])


SPECS: list[dict] = []


def spec(
    block: str,
    number: int,
    title: str,
    statement: str,
    input_format: str,
    output_format: str,
    sample: str,
    cases: list[str],
    ref: Callable[[str], str],
) -> None:
    task_id = f"{block}-{number:02d}"
    if len(cases) < 6:
        raise ValueError(f"{task_id}: need at least 6 hidden tests")
    unique_cases = list(dict.fromkeys(cases))
    tests = [{"input": case.strip("\n"), "output": ref(case).strip("\n")} for case in unique_cases]
    sample_output = ref(sample).strip("\n")
    SPECS.append(
        {
            "id": task_id,
            "block": block,
            "block_title": BLOCKS[block],
            "number": number,
            "code": f"{'If' if block == 'if' else block.capitalize()}{number}",
            "title": title,
            "statement": statement.strip(),
            "input_format": input_format.strip(),
            "output_format": output_format.strip(),
            "sample_input": sample.strip("\n"),
            "sample_output": sample_output,
            "tests": tests,
            "ref": ref,
        }
    )


def main() -> None:
    build_integer()
    build_if()
    build_for()
    build_proc()
    build_series()
    assert len(SPECS) == 100, len(SPECS)
    for block in BLOCKS:
        assert sum(1 for item in SPECS if item["block"] == block) == 20, block
    for item in SPECS:
        assert item["tests"], item["id"]
    public_specs = [{key: value for key, value in item.items() if key != "ref"} for item in SPECS]
    OUT.write_text(json.dumps(public_specs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total_tests = sum(len(item["tests"]) for item in SPECS)
    print(f"wrote {OUT} ({len(SPECS)} tasks, {total_tests} hidden tests)")


def build_integer() -> None:
    spec(
        "integer", 1, "Полные метры",
        "Дано расстояние L в сантиметрах. Используя операцию деления нацело, "
        "найти количество полных метров в нём (1 метр = 100 см).",
        "Одно целое число L — расстояние в сантиметрах.",
        "Одно целое число — количество полных метров.",
        "1234", ["1234", "0", "99", "100", "250", "999", "100000", "7"],
        solve_integer_1,
    )
    spec(
        "integer", 2, "Полные тонны",
        "Дана масса M в килограммах. Используя операцию деления нацело, "
        "найти количество полных тонн в ней (1 тонна = 1000 кг).",
        "Одно целое число M — масса в килограммах.",
        "Одно целое число — количество полных тонн.",
        "3450", ["3450", "0", "999", "1000", "2500", "999999", "1", "7250"],
        solve_integer_2,
    )
    spec(
        "integer", 3, "Полные килобайты",
        "Дан размер файла в байтах. Используя операцию деления нацело, "
        "найти количество полных килобайтов, которые занимает данный файл "
        "(1 килобайт = 1024 байта).",
        "Одно целое число — размер файла в байтах.",
        "Одно целое число — количество полных килобайтов.",
        "5000", ["5000", "0", "1023", "1024", "2048", "10000", "1", "777777"],
        solve_integer_3,
    )
    spec(
        "integer", 4, "Отрезки на отрезке",
        "Даны целые положительные числа A и B (A > B). На отрезке длины A "
        "размещено максимально возможное количество отрезков длины B "
        "(без наложений). Используя операцию деления нацело, найти количество "
        "отрезков B, размещённых на отрезке A.",
        "Два целых числа A и B, каждое на новой строке (A > B > 0).",
        "Одно целое число — количество отрезков B.",
        "10\n3", ["10\n3", "20\n5", "7\n2", "100\n7", "9\n4", "16\n15", "11\n1", "50\n8"],
        solve_integer_4,
    )
    spec(
        "integer", 5, "Остаток отрезка",
        "Даны целые положительные числа A и B (A > B). На отрезке длины A "
        "размещено максимально возможное количество отрезков длины B "
        "(без наложений). Используя операцию взятия остатка от деления нацело, "
        "найти длину незанятой части отрезка A.",
        "Два целых числа A и B, каждое на новой строке (A > B > 0).",
        "Одно целое число — длина незанятой части.",
        "10\n3", ["10\n3", "20\n5", "7\n2", "100\n7", "9\n4", "16\n15", "11\n1", "50\n8"],
        solve_integer_5,
    )
    spec(
        "integer", 6, "Цифры двузначного числа",
        "Дано двузначное число. Вывести вначале его левую цифру (десятки), "
        "а затем — его правую цифру (единицы). Для нахождения десятков "
        "использовать операцию деления нацело, для нахождения единиц — "
        "операцию взятия остатка от деления.",
        "Одно двузначное целое число (10–99).",
        "Два целых числа: сначала десятки, затем единицы.",
        "47", ["47", "10", "99", "23", "58", "61", "72", "85"],
        solve_integer_6,
    )
    spec(
        "integer", 7, "Сумма и произведение цифр",
        "Дано двузначное число. Найти сумму и произведение его цифр.",
        "Одно двузначное целое число (10–99).",
        "Два целых числа: сумма цифр, затем их произведение.",
        "47", ["47", "10", "99", "23", "58", "61", "72", "85"],
        solve_integer_7,
    )
    spec(
        "integer", 8, "Перестановка цифр",
        "Дано двузначное число. Вывести число, полученное при перестановке "
        "цифр исходного числа.",
        "Одно двузначное целое число (10–99).",
        "Одно целое число — результат перестановки цифр.",
        "47", ["47", "10", "99", "23", "58", "61", "72", "85"],
        solve_integer_8,
    )
    spec(
        "integer", 9, "Сотни",
        "Дано трёхзначное число. Используя одну операцию деления нацело, "
        "вывести первую цифру данного числа (сотни).",
        "Одно трёхзначное целое число (100–999).",
        "Одно целое число — цифра сотен.",
        "123", ["123", "100", "999", "456", "780", "305", "864", "291"],
        solve_integer_9,
    )
    spec(
        "integer", 10, "Единицы и десятки",
        "Дано трёхзначное число. Вывести вначале его последнюю цифру "
        "(единицы), а затем — его среднюю цифру (десятки).",
        "Одно трёхзначное целое число (100–999).",
        "Два целых числа: единицы, затем десятки.",
        "123", ["123", "100", "999", "456", "780", "305", "864", "291"],
        solve_integer_10,
    )
    spec(
        "integer", 11, "Сумма и произведение трёх цифр",
        "Дано трёхзначное число. Найти сумму и произведение его цифр.",
        "Одно трёхзначное целое число (100–999).",
        "Два целых числа: сумма цифр, затем их произведение.",
        "123", ["123", "100", "999", "456", "780", "305", "864", "291"],
        solve_integer_11,
    )
    spec(
        "integer", 12, "Число справа налево",
        "Дано трёхзначное число. Вывести число, полученное при прочтении "
        "исходного числа справа налево.",
        "Одно трёхзначное целое число (100–999).",
        "Одно целое число — прочитанное справа налево.",
        "123", ["123", "100", "999", "456", "780", "305", "864", "291"],
        solve_integer_12,
    )
    spec(
        "integer", 13, "Первую цифру — в конец",
        "Дано трёхзначное число. В нём зачеркнули первую слева цифру "
        "и приписали её справа. Вывести полученное число.",
        "Одно трёхзначное целое число (100–999).",
        "Одно целое число — результат преобразования.",
        "123", ["123", "100", "999", "456", "780", "305", "864", "291"],
        solve_integer_13,
    )
    spec(
        "integer", 14, "Последнюю цифру — в начало",
        "Дано трёхзначное число. В нём зачеркнули первую справа цифру "
        "и приписали её слева. Вывести полученное число.",
        "Одно трёхзначное целое число (100–999).",
        "Одно целое число — результат преобразования.",
        "123", ["123", "100", "999", "456", "780", "305", "864", "291"],
        solve_integer_14,
    )
    spec(
        "integer", 15, "Перестановка сотен и десятков",
        "Дано трёхзначное число. Вывести число, полученное при перестановке "
        "цифр сотен и десятков исходного числа (например, 123 перейдёт в 213).",
        "Одно трёхзначное целое число (100–999).",
        "Одно целое число — результат перестановки.",
        "123", ["123", "100", "999", "456", "780", "305", "864", "291"],
        solve_integer_15,
    )
    spec(
        "integer", 16, "Перестановка десятков и единиц",
        "Дано трёхзначное число. Вывести число, полученное при перестановке "
        "цифр десятков и единиц исходного числа (например, 123 перейдёт в 132).",
        "Одно трёхзначное целое число (100–999).",
        "Одно целое число — результат перестановки.",
        "123", ["123", "100", "999", "456", "780", "305", "864", "291"],
        solve_integer_16,
    )
    spec(
        "integer", 17, "Разряд сотен",
        "Дано целое число, большее 999. Используя одну операцию деления нацело "
        "и одну операцию взятия остатка от деления, найти цифру, "
        "соответствующую разряду сотен в записи этого числа.",
        "Одно целое число, большее 999.",
        "Одно целое число — цифра разряда сотен.",
        "12345", ["12345", "1000", "9999", "45678", "100000", "780123", "3050", "999999"],
        solve_integer_17,
    )
    spec(
        "integer", 18, "Разряд тысяч",
        "Дано целое число, большее 999. Используя одну операцию деления нацело "
        "и одну операцию взятия остатка от деления, найти цифру, "
        "соответствующую разряду тысяч в записи этого числа.",
        "Одно целое число, большее 999.",
        "Одно целое число — цифра разряда тысяч.",
        "12345", ["12345", "1000", "9999", "45678", "100000", "780123", "3050", "999999"],
        solve_integer_18,
    )
    spec(
        "integer", 19, "Полные минуты",
        "С начала суток прошло N секунд (N — целое). Найти количество полных "
        "минут, прошедших с начала суток.",
        "Одно целое неотрицательное число N — секунды.",
        "Одно целое число — количество полных минут.",
        "3725", ["3725", "0", "59", "60", "61", "3599", "3600", "86399"],
        solve_integer_19,
    )
    spec(
        "integer", 20, "Полные часы",
        "С начала суток прошло N секунд (N — целое). Найти количество полных "
        "часов, прошедших с начала суток.",
        "Одно целое неотрицательное число N — секунды.",
        "Одно целое число — количество полных часов.",
        "3725", ["3725", "0", "3599", "3600", "3601", "7200", "86399", "59"],
        solve_integer_20,
    )


def build_if() -> None:
    spec(
        "if", 1, "Положительное число + 1",
        "Дано целое число. Если оно является положительным, то прибавить "
        "к нему 1; в противном случае не изменять его. Вывести полученное число.",
        "Одно целое число.",
        "Одно целое число — результат.",
        "7", ["7", "-3", "0", "1", "-1", "42", "-100", "10"],
        solve_if_1,
    )
    spec(
        "if", 2, "Плюс один или минус два",
        "Дано целое число. Если оно является положительным, то прибавить "
        "к нему 1; в противном случае вычесть из него 2. Вывести полученное число.",
        "Одно целое число.",
        "Одно целое число — результат.",
        "7", ["7", "-3", "0", "1", "-1", "42", "-100", "10"],
        solve_if_2,
    )
    spec(
        "if", 3, "Три случая",
        "Дано целое число. Если оно является положительным, то прибавить "
        "к нему 1; если отрицательным, то вычесть из него 2; если нулевым, "
        "то заменить его на 10. Вывести полученное число.",
        "Одно целое число.",
        "Одно целое число — результат.",
        "7", ["7", "-3", "0", "1", "-1", "42", "-100", "10"],
        solve_if_3,
    )
    spec(
        "if", 4, "Положительные из трёх",
        "Даны три целых числа. Найти количество положительных чисел "
        "в исходном наборе.",
        "Три целых числа, каждое на новой строке.",
        "Одно целое число — количество положительных.",
        "5\n-2\n0", ["5\n-2\n0", "1\n2\n3", "-1\n-2\n-3", "0\n0\n0", "10\n-1\n7", "-5\n4\n-6", "9\n8\n-7", "1\n0\n-1"],
        solve_if_4,
    )
    spec(
        "if", 5, "Положительные и отрицательные",
        "Даны три целых числа. Найти количество положительных и количество "
        "отрицательных чисел в исходном наборе.",
        "Три целых числа, каждое на новой строке.",
        "Два целых числа: количество положительных, затем отрицательных.",
        "5\n-2\n0", ["5\n-2\n0", "1\n2\n3", "-1\n-2\n-3", "0\n0\n0", "10\n-1\n7", "-5\n4\n-6", "9\n8\n-7", "1\n0\n-1"],
        solve_if_5,
    )
    spec(
        "if", 6, "Большее из двух",
        "Даны два числа. Вывести большее из них.",
        "Два целых числа, каждое на новой строке.",
        "Одно целое число — большее.",
        "12\n7", ["12\n7", "-3\n-8", "0\n5", "100\n99", "4\n4", "-1\n1", "25\n-25", "7\n70"],
        solve_if_6,
    )
    spec(
        "if", 7, "Номер меньшего",
        "Даны два числа. Вывести порядковый номер меньшего из них.",
        "Два целых числа, каждое на новой строке.",
        "Одно целое число — 1 или 2.",
        "12\n7", ["12\n7", "7\n12", "-3\n-8", "0\n5", "100\n99", "-1\n1", "25\n-25", "5\n0"],
        solve_if_7,
    )
    spec(
        "if", 8, "Большее, затем меньшее",
        "Даны два числа. Вывести вначале большее, а затем меньшее из них.",
        "Два целых числа, каждое на новой строке.",
        "Два целых числа: большее, затем меньшее.",
        "12\n7", ["12\n7", "7\n12", "-3\n-8", "0\n5", "100\n99", "-1\n1", "25\n-25", "5\n0"],
        solve_if_8,
    )
    spec(
        "if", 9, "Меньшее в A",
        "Даны две переменные вещественного типа: A, B. Перераспределить "
        "значения данных переменных так, чтобы в A оказалось меньшее "
        "из значений, а в B — большее. Вывести новые значения переменных A и B.",
        "Два вещественных числа A и B, каждое на новой строке.",
        "Два вещественных числа: меньшее, затем большее.",
        "3.5\n1.25", ["3.5\n1.25", "1\n2", "-4\n4", "0\n-1", "10.5\n2.5", "-7\n-3", "0.1\n0.2", "5\n5"],
        solve_if_9,
    )
    spec(
        "if", 10, "Сумма или нули",
        "Даны две переменные целого типа: A и B. Если их значения не равны, "
        "то присвоить каждой переменной сумму этих значений, а если равны, "
        "то присвоить переменным нулевые значения. Вывести новые значения A и B.",
        "Два целых числа A и B, каждое на новой строке.",
        "Два целых числа — новые значения A и B.",
        "3\n5", ["3\n5", "4\n4", "-2\n7", "0\n0", "-5\n-5", "10\n-3", "1\n2", "100\n100"],
        solve_if_10,
    )
    spec(
        "if", 11, "Максимум или нули",
        "Даны две переменные целого типа: A и B. Если их значения не равны, "
        "то присвоить каждой переменной большее из этих значений, а если равны, "
        "то присвоить переменным нулевые значения. Вывести новые значения A и B.",
        "Два целых числа A и B, каждое на новой строке.",
        "Два целых числа — новые значения A и B.",
        "3\n5", ["3\n5", "4\n4", "-2\n7", "0\n0", "-5\n-5", "10\n-3", "1\n2", "100\n100"],
        solve_if_11,
    )
    spec(
        "if", 12, "Наименьшее из трёх",
        "Даны три числа. Найти наименьшее из них.",
        "Три целых числа, каждое на новой строке.",
        "Одно целое число — наименьшее.",
        "8\n3\n5", ["8\n3\n5", "1\n2\n3", "3\n2\n1", "-1\n0\n1", "5\n5\n5", "10\n-10\n0", "7\n7\n3", "0\n9\n-9"],
        solve_if_12,
    )
    spec(
        "if", 13, "Среднее из трёх",
        "Даны три числа. Найти среднее из них (то есть число, расположенное "
        "между наименьшим и наибольшим).",
        "Три целых числа, каждое на новой строке.",
        "Одно целое число — среднее значение.",
        "8\n3\n5", ["8\n3\n5", "1\n2\n3", "3\n2\n1", "-1\n0\n1", "5\n5\n5", "10\n-10\n0", "7\n7\n3", "0\n9\n-9"],
        solve_if_13,
    )
    spec(
        "if", 14, "Наименьшее, затем наибольшее",
        "Даны три числа. Вывести вначале наименьшее, а затем наибольшее "
        "из данных чисел.",
        "Три целых числа, каждое на новой строке.",
        "Два целых числа: наименьшее, затем наибольшее.",
        "8\n3\n5", ["8\n3\n5", "1\n2\n3", "3\n2\n1", "-1\n0\n1", "5\n5\n5", "10\n-10\n0", "7\n7\n3", "0\n9\n-9"],
        solve_if_14,
    )
    spec(
        "if", 15, "Сумма двух наибольших",
        "Даны три числа. Найти сумму двух наибольших из них.",
        "Три целых числа, каждое на новой строке.",
        "Одно целое число — сумма двух наибольших.",
        "8\n3\n5", ["8\n3\n5", "1\n2\n3", "3\n2\n1", "-1\n0\n1", "5\n5\n5", "10\n-10\n0", "7\n7\n3", "0\n9\n-9"],
        solve_if_15,
    )
    spec(
        "if", 16, "Удвоить или изменить знак",
        "Даны три переменные вещественного типа: A, B, C. Если их значения "
        "упорядочены по возрастанию, то удвоить их; в противном случае заменить "
        "значение каждой переменной на противоположное. Вывести новые значения "
        "переменных A, B, C.",
        "Три вещественных числа A, B, C, каждое на новой строке.",
        "Три вещественных числа — новые значения A, B, C.",
        "1\n2\n3", ["1\n2\n3", "3\n2\n1", "1\n3\n2", "-1\n0\n2", "2.5\n3.5\n4.5", "0\n0\n0", "-3\n-2\n-1", "5\n1\n9"],
        solve_if_16,
    )
    spec(
        "if", 17, "Упорядочены любым способом",
        "Даны три переменные вещественного типа: A, B, C. Если их значения "
        "упорядочены по возрастанию или убыванию, то удвоить их; в противном "
        "случае заменить значение каждой переменной на противоположное. "
        "Вывести новые значения переменных A, B, C.",
        "Три вещественных числа A, B, C, каждое на новой строке.",
        "Три вещественных числа — новые значения A, B, C.",
        "1\n2\n3", ["1\n2\n3", "3\n2\n1", "1\n3\n2", "-1\n0\n2", "2.5\n3.5\n4.5", "0\n0\n0", "-3\n-2\n-1", "5\n1\n9"],
        solve_if_17,
    )
    spec(
        "if", 18, "Отличное из трёх",
        "Даны три целых числа, одно из которых отлично от двух других, "
        "равных между собой. Определить порядковый номер числа, отличного "
        "от остальных.",
        "Три целых числа, каждое на новой строке. Ровно два из них равны.",
        "Одно целое число — порядковый номер отличного числа (1–3).",
        "5\n5\n9", ["5\n5\n9", "7\n2\n7", "1\n8\n8", "-3\n-3\n0", "10\n10\n4", "0\n6\n0", "12\n12\n13", "3\n4\n4"],
        solve_if_18,
    )
    spec(
        "if", 19, "Отличное из четырёх",
        "Даны четыре целых числа, одно из которых отлично от трёх других, "
        "равных между собой. Определить порядковый номер числа, отличного "
        "от остальных.",
        "Четыре целых числа, каждое на новой строке. Ровно три из них равны.",
        "Одно целое число — порядковый номер отличного числа (1–4).",
        "5\n5\n5\n9", ["5\n5\n5\n9", "7\n2\n7\n7", "1\n8\n8\n8", "-3\n-3\n-3\n0", "10\n12\n10\n10", "0\n6\n0\n0", "12\n12\n13\n12", "3\n4\n4\n4"],
        solve_if_19,
    )
    spec(
        "if", 20, "Ближайшая точка",
        "На числовой оси расположены три точки: A, B, C. Определить, какая "
        "из двух последних точек (B или C) расположена ближе к A, и вывести "
        "эту точку и её расстояние от точки A.",
        "Три вещественных числа A, B, C, каждое на новой строке.",
        "Два числа: координата ближайшей точки и расстояние до A.",
        "2\n7\n-3", ["2\n7\n-3", "0\n5\n7", "-4\n-1\n-9", "10\n3\n12", "1.5\n2.5\n0.5", "-2\n0\n-4", "8\n9\n7", "100\n90\n110"],
        solve_if_20,
    )


def build_for() -> None:
    spec(
        "for", 1, "Число K повторяется N раз",
        "Даны целые числа K и N (N > 0). Вывести N раз число K.",
        "Два целых числа K и N, каждое на новой строке (N > 0).",
        "N целых чисел в одну строку.",
        "4\n3", ["4\n3", "1\n1", "0\n5", "-2\n4", "7\n2", "10\n10", "-5\n3", "3\n7"],
        solve_for_1,
    )
    spec(
        "for", 2, "Возрастающая последовательность",
        "Даны два целых числа A и B (A < B). Вывести в порядке возрастания "
        "все целые числа, расположенные между A и B (включая сами числа A и B), "
        "а также количество N этих чисел.",
        "Два целых числа A и B, каждое на новой строке (A < B).",
        "Все числа от A до B, затем их количество.",
        "3\n7", ["3\n7", "1\n2", "0\n5", "-3\n2", "10\n15", "-5\n-1", "7\n8", "20\n25"],
        solve_for_2,
    )
    spec(
        "for", 3, "Убывающая последовательность",
        "Даны два целых числа A и B (A < B). Вывести в порядке убывания "
        "все целые числа, расположенные между A и B (не включая числа A и B), "
        "а также количество N этих чисел.",
        "Два целых числа A и B, каждое на новой строке (A < B).",
        "Числа между A и B по убыванию, затем их количество. Если чисел нет — 0.",
        "3\n7", ["3\n7", "1\n2", "0\n5", "-3\n2", "10\n15", "-5\n-1", "7\n8", "20\n25"],
        solve_for_3,
    )
    spec(
        "for", 4, "Стоимость 1–10 кг",
        "Дано вещественное число — цена 1 кг конфет. Вывести стоимость "
        "1, 2, …, 10 кг конфет.",
        "Одно вещественное число — цена 1 кг.",
        "10 вещественных чисел — стоимость 1, 2, …, 10 кг.",
        "150.5", ["150.5", "10", "0", "99.9", "1.25", "200", "3.75", "999.99"],
        solve_for_4,
    )
    spec(
        "for", 5, "Стоимость 0.1–1 кг",
        "Дано вещественное число — цена 1 кг конфет. Вывести стоимость "
        "0.1, 0.2, …, 1 кг конфет.",
        "Одно вещественное число — цена 1 кг.",
        "10 вещественных чисел — стоимость 0.1, 0.2, …, 1 кг.",
        "150.5", ["150.5", "10", "0", "99.9", "1.25", "200", "3.75", "999.99"],
        solve_for_5,
    )
    spec(
        "for", 6, "Стоимость 1.2–2 кг",
        "Дано вещественное число — цена 1 кг конфет. Вывести стоимость "
        "1.2, 1.4, …, 2 кг конфет.",
        "Одно вещественное число — цена 1 кг.",
        "5 вещественных чисел — стоимость 1.2, 1.4, …, 2 кг.",
        "150.5", ["150.5", "10", "0", "99.9", "1.25", "200", "3.75", "999.99"],
        solve_for_6,
    )
    spec(
        "for", 7, "Сумма целых",
        "Даны два целых числа A и B (A < B). Найти сумму всех целых чисел "
        "от A до B включительно.",
        "Два целых числа A и B, каждое на новой строке (A < B).",
        "Одно целое число — сумма.",
        "1\n10", ["1\n10", "-3\n3", "0\n5", "-10\n-5", "100\n105", "-1\n1", "5\n6", "7\n20"],
        solve_for_7,
    )
    spec(
        "for", 8, "Произведение целых",
        "Даны два целых числа A и B (A < B). Найти произведение всех целых "
        "чисел от A до B включительно.",
        "Два целых числа A и B, каждое на новой строке (A < B).",
        "Одно целое число — произведение.",
        "1\n5", ["1\n5", "2\n4", "-2\n3", "5\n7", "1\n10", "-3\n-1", "10\n12", "0\n4"],
        solve_for_8,
    )
    spec(
        "for", 9, "Сумма квадратов",
        "Даны два целых числа A и B (A < B). Найти сумму квадратов всех целых "
        "чисел от A до B включительно.",
        "Два целых числа A и B, каждое на новой строке (A < B).",
        "Одно целое число — сумма квадратов.",
        "1\n5", ["1\n5", "-3\n3", "0\n5", "-10\n-5", "2\n4", "-2\n2", "5\n7", "10\n12"],
        solve_for_9,
    )
    spec(
        "for", 10, "Гармоническая сумма",
        "Дано целое число N (> 0). Найти сумму 1 + 1/2 + 1/3 + … + 1/N "
        "(вещественное число).",
        "Одно целое число N (N > 0).",
        "Одно вещественное число — сумма.",
        "5", ["5", "1", "2", "10", "50", "100", "7", "3"],
        solve_for_10,
    )
    spec(
        "for", 11, "Сумма квадратов от N до 2N",
        "Дано целое число N (> 0). Найти сумму N² + (N+1)² + (N+2)² + … + (2·N)² "
        "(целое число).",
        "Одно целое число N (N > 0).",
        "Одно целое число — сумма.",
        "3", ["3", "1", "2", "5", "10", "20", "7", "4"],
        solve_for_11,
    )
    spec(
        "for", 12, "Произведение десятичных дробей",
        "Дано целое число N (> 0). Найти произведение 1.1 · 1.2 · 1.3 · … "
        "(N сомножителей).",
        "Одно целое число N (N > 0).",
        "Одно вещественное число — произведение.",
        "5", ["5", "1", "2", "10", "20", "3", "7", "12"],
        solve_for_12,
    )
    spec(
        "for", 13, "Знакочередующаяся сумма",
        "Дано целое число N (> 0). Найти значение выражения 1.1 − 1.2 + 1.3 − … "
        "(N слагаемых, знаки чередуются). Условный оператор не использовать.",
        "Одно целое число N (N > 0).",
        "Одно вещественное число — значение выражения.",
        "5", ["5", "1", "2", "10", "20", "3", "7", "12"],
        solve_for_13,
    )
    spec(
        "for", 14, "Квадраты через нечётные числа",
        "Дано целое число N (> 0). Найти квадрат данного числа, используя "
        "формулу N² = 1 + 3 + 5 + … + (2·N − 1). После добавления к сумме "
        "каждого слагаемого выводить текущее значение суммы (в результате "
        "будут выведены квадраты всех целых чисел от 1 до N).",
        "Одно целое число N (N > 0).",
        "N целых чисел — квадраты чисел от 1 до N.",
        "5", ["5", "1", "2", "3", "10", "7", "12", "20"],
        solve_for_14,
    )
    spec(
        "for", 15, "Степень A^N",
        "Дано вещественное число A и целое число N (> 0). Найти A в степени N: "
        "A^N = A · A · … · A (числа A перемножаются N раз).",
        "Вещественное A и целое N, каждое на новой строке (N > 0).",
        "Одно вещественное число — A^N.",
        "2\n10", ["2\n10", "1.5\n3", "-2\n3", "10\n1", "0.5\n4", "-1\n5", "3\n4", "1.1\n10"],
        solve_for_15,
    )
    spec(
        "for", 16, "Все степени A",
        "Дано вещественное число A и целое число N (> 0). Используя один цикл, "
        "вывести все целые степени числа A от 1 до N.",
        "Вещественное A и целое N, каждое на новой строке (N > 0).",
        "N вещественных чисел — A^1, A^2, …, A^N.",
        "2\n5", ["2\n5", "1.5\n3", "-2\n4", "10\n1", "0.5\n4", "-1\n5", "3\n4", "1.1\n5"],
        solve_for_16,
    )
    spec(
        "for", 17, "Сумма степеней",
        "Дано вещественное число A и целое число N (> 0). Используя один цикл, "
        "найти сумму 1 + A + A² + A³ + … + A^N.",
        "Вещественное A и целое N, каждое на новой строке (N > 0).",
        "Одно вещественное число — сумма.",
        "2\n5", ["2\n5", "1.5\n3", "-2\n4", "10\n1", "0.5\n4", "-1\n5", "3\n4", "1.1\n5"],
        solve_for_17,
    )
    spec(
        "for", 18, "Знакочередующиеся степени",
        "Дано вещественное число A и целое число N (> 0). Используя один цикл, "
        "найти значение выражения 1 − A + A² − A³ + … + (−1)^N·A^N. "
        "Условный оператор не использовать.",
        "Вещественное A и целое N, каждое на новой строке (N > 0).",
        "Одно вещественное число — значение выражения.",
        "2\n5", ["2\n5", "1.5\n3", "-2\n4", "10\n1", "0.5\n4", "-1\n5", "3\n4", "1.1\n5"],
        solve_for_18,
    )
    spec(
        "for", 19, "Факториал",
        "Дано целое число N (> 0). Найти произведение N! = 1 · 2 · … · N "
        "(N-факториал). Чтобы избежать целочисленного переполнения, вычислять "
        "это произведение с помощью вещественной переменной и вывести его "
        "как вещественное число.",
        "Одно целое число N (N > 0).",
        "Одно вещественное число — N!.",
        "5", ["5", "1", "2", "3", "10", "20", "30", "50"],
        solve_for_19,
    )
    spec(
        "for", 20, "Сумма факториалов",
        "Дано целое число N (> 0). Используя один цикл, найти сумму "
        "1! + 2! + 3! + … + N! (выражение N! — N-факториал — обозначает "
        "произведение всех целых чисел от 1 до N: N! = 1 · 2 · … · N). "
        "Чтобы избежать целочисленного переполнения, проводить вычисления "
        "с помощью вещественных переменных и вывести результат как "
        "вещественное число.",
        "Одно целое число N (N > 0).",
        "Одно вещественное число — сумма факториалов.",
        "5", ["5", "1", "2", "3", "10", "20", "30", "50"],
        solve_for_20,
    )


def build_proc() -> None:
    spec(
        "proc", 1, "Третьи степени",
        "Описать процедуру PowerA3(A, B), вычисляющую третью степень числа A "
        "и возвращающую её в переменной B. С помощью этой процедуры найти "
        "третьи степени пяти данных чисел.",
        "Пять вещественных чисел, каждое на новой строке.",
        "Пять вещественных чисел — третьи степени.",
        "2\n3\n4\n5\n6", ["2\n3\n4\n5\n6", "0\n1\n-1\n10\n0.5", "-2\n-3\n-4\n-5\n-6", "1.5\n2.5\n3.5\n4.5\n5.5", "10\n20\n30\n40\n50", "-1\n0\n1\n2\n-2", "7\n8\n9\n10\n11", "0.1\n0.2\n0.3\n0.4\n0.5"],
        solve_proc_1,
    )
    spec(
        "proc", 2, "Вторая, третья и четвёртая степени",
        "Описать процедуру PowerA234(A, B, C, D), вычисляющую вторую, третью "
        "и четвёртую степень числа A и возвращающую эти степени соответственно "
        "в переменных B, C и D. С помощью этой процедуры найти вторую, третью "
        "и четвёртую степени пяти данных чисел.",
        "Пять вещественных чисел, каждое на новой строке.",
        "Для каждого числа — три числа: квадрат, куб, четвёртая степень.",
        "2\n3\n4\n5\n6", ["2\n3\n4\n5\n6", "0\n1\n-1\n10\n0.5", "-2\n-3\n-4\n-5\n-6", "1.5\n2.5\n3.5\n4.5\n5.5", "10\n20\n30\n40\n50", "-1\n0\n1\n2\n-2", "7\n8\n9\n10\n11", "0.1\n0.2\n0.3\n0.4\n0.5"],
        solve_proc_2,
    )
    spec(
        "proc", 3, "Средние арифметическое и геометрическое",
        "Описать процедуру Mean(X, Y, AMean, GMean), вычисляющую среднее "
        "арифметическое AMean = (X + Y)/2 и среднее геометрическое "
        "GMean = √(X·Y) двух положительных чисел X и Y. С помощью этой "
        "процедуры найти среднее арифметическое и среднее геометрическое "
        "для пар (A, B), (A, C), (A, D), если даны A, B, C, D.",
        "Четыре положительных вещественных числа A, B, C, D, каждое на новой строке.",
        "Для пар (A,B), (A,C), (A,D) — сначала среднее арифметическое, затем среднее геометрическое.",
        "2\n8\n18\n32", ["2\n8\n18\n32", "1\n1\n1\n1", "4\n9\n16\n25", "0.5\n2\n8\n18", "10\n20\n30\n40", "3\n3\n3\n3", "2.5\n6.25\n10\n15", "1\n4\n9\n16"],
        solve_proc_3,
    )
    spec(
        "proc", 4, "Равносторонние треугольники",
        "Описать процедуру TrianglePS(a, P, S), вычисляющую по стороне a "
        "равностороннего треугольника его периметр P = 3·a и площадь "
        "S = a²·√3/4. С помощью этой процедуры найти периметры и площади "
        "трёх равносторонних треугольников с данными сторонами.",
        "Три положительных вещественных числа — стороны, каждое на новой строке.",
        "Для каждого треугольника — периметр, затем площадь.",
        "3\n4\n5", ["3\n4\n5", "1\n1\n1", "2\n6\n10", "0.5\n1.5\n2.5", "10\n20\n30", "7\n8\n9", "1.25\n2.25\n3.25", "100\n200\n300"],
        solve_proc_4,
    )
    spec(
        "proc", 5, "Прямоугольники по вершинам",
        "Описать процедуру RectPS(x1, y1, x2, y2, P, S), вычисляющую периметр P "
        "и площадь S прямоугольника со сторонами, параллельными осям координат, "
        "по координатам (x1, y1), (x2, y2) его противоположных вершин. "
        "С помощью этой процедуры найти периметры и площади трёх прямоугольников "
        "с данными противоположными вершинами.",
        "12 вещественных чисел: для каждого из трёх прямоугольников — x1, y1, x2, y2.",
        "Для каждого прямоугольника — периметр, затем площадь.",
        "0\n0\n3\n4\n1\n2\n5\n7\n-1\n-1\n2\n2",
        ["0\n0\n3\n4\n1\n2\n5\n7\n-1\n-1\n2\n2", "0\n0\n1\n1\n2\n2\n6\n8\n-3\n-4\n1\n2", "1\n1\n2\n3\n2\n2\n2\n2\n3\n3\n3\n3", "-5\n-5\n5\n5\n0\n0\n10\n2\n-2\n3\n4\n9", "10\n10\n20\n15\n-3\n2\n4\n8\n1\n1\n2\n1", "0\n0\n100\n50\n-10\n-10\n-5\n-6\n3\n7\n9\n11", "2\n3\n2\n9\n4\n1\n1\n5\n0\n0\n0\n0", "1.5\n2.5\n4.5\n6.5\n-1\n-1\n1\n1\n0.5\n0.5\n2.5\n4.5"],
        solve_proc_5,
    )
    spec(
        "proc", 6, "Количество и сумма цифр",
        "Описать процедуру DigitCountSum(K, C, S), находящую количество C цифр "
        "целого положительного числа K, а также их сумму S. С помощью этой "
        "процедуры найти количество и сумму цифр для каждого из пяти данных "
        "целых чисел.",
        "Пять целых положительных чисел, каждое на новой строке.",
        "Для каждого числа — количество цифр, затем сумма цифр.",
        "123\n4567\n9\n1000\n987654", ["123\n4567\n9\n1000\n987654", "1\n2\n3\n4\n5", "10\n20\n30\n40\n50", "999\n100\n101\n202\n303", "7\n77\n777\n7777\n77777", "12\n345\n6789\n10101\n202020", "5\n55\n555\n5555\n55555", "100000\n999999\n123456\n654321\n111111"],
        solve_proc_6,
    )
    spec(
        "proc", 7, "Обратный порядок цифр",
        "Описать процедуру InvDigits(K), меняющую порядок следования цифр "
        "целого положительного числа K на обратный. С помощью этой процедуры "
        "поменять порядок следования цифр на обратный для каждого из пяти "
        "данных целых чисел.",
        "Пять целых положительных чисел, каждое на новой строке.",
        "Пять целых чисел — числа с обратным порядком цифр.",
        "123\n4567\n9\n1000\n987654", ["123\n4567\n9\n1000\n987654", "10\n20\n30\n40\n50", "100\n200\n300\n400\n500", "111\n222\n333\n444\n555", "123456\n654321\n111111\n222222\n333333", "1\n2\n3\n4\n5", "9009\n808\n707\n606\n505", "12\n345\n6789\n10101\n202020"],
        solve_proc_7,
    )
    spec(
        "proc", 8, "Цифра справа",
        "Описать процедуру AddRightDigit(D, K), добавляющую к целому "
        "положительному числу K справа цифру D (D — входной параметр целого "
        "типа, лежащий в диапазоне 0–9, K — параметр целого типа, являющийся "
        "одновременно входным и выходным). С помощью этой процедуры "
        "последовательно добавить к данному числу K справа данные цифры D1 "
        "и D2, выводя результат каждого добавления.",
        "Три целых числа K, D1, D2, каждое на новой строке (K > 0, 0 ≤ D ≤ 9).",
        "Два целых числа: результат после добавления D1 и после добавления D2.",
        "12\n3\n4", ["12\n3\n4", "5\n0\n0", "999\n9\n9", "1\n0\n5", "5\n1\n2", "123\n4\n5", "10\n2\n7", "987654\n3\n8"],
        solve_proc_8,
    )
    spec(
        "proc", 9, "Цифра слева",
        "Описать процедуру AddLeftDigit(D, K), добавляющую к целому "
        "положительному числу K слева цифру D (D — входной параметр целого "
        "типа, лежащий в диапазоне 1–9, K — параметр целого типа, являющийся "
        "одновременно входным и выходным). С помощью этой процедуры "
        "последовательно добавить к данному числу K слева данные цифры D1 "
        "и D2, выводя результат каждого добавления.",
        "Три целых числа K, D1, D2, каждое на новой строке (K > 0, 1 ≤ D ≤ 9).",
        "Два целых числа: результат после добавления D1 и после добавления D2.",
        "12\n3\n4", ["12\n3\n4", "5\n1\n2", "999\n9\n8", "1\n1\n1", "123\n4\n5", "10\n2\n7", "987654\n3\n8", "42\n9\n1"],
        solve_proc_9,
    )
    spec(
        "proc", 10, "Обмен значений",
        "Описать процедуру Swap(X, Y), меняющую содержимое переменных X и Y. "
        "С её помощью для данных переменных A, B, C, D последовательно поменять "
        "содержимое следующих пар: A и B, C и D, B и C, и вывести новые "
        "значения A, B, C, D.",
        "Четыре вещественных числа A, B, C, D, каждое на новой строке.",
        "Четыре вещественных числа — новые значения A, B, C, D.",
        "1\n2\n3\n4", ["1\n2\n3\n4", "10\n20\n30\n40", "-1\n-2\n-3\n-4", "0.5\n1.5\n2.5\n3.5", "5\n5\n5\n5", "1.1\n2.2\n3.3\n4.4", "-10\n0\n10\n20", "7\n3\n9\n1"],
        solve_proc_10,
    )
    spec(
        "proc", 11, "Минимум и максимум из четырёх",
        "Описать процедуру Minmax(X, Y), записывающую в переменную X "
        "минимальное из значений X и Y, а в переменную Y — максимальное "
        "из этих значений. Используя четыре вызова этой процедуры, найти "
        "минимальное и максимальное из данных чисел A, B, C, D.",
        "Четыре вещественных числа A, B, C, D, каждое на новой строке.",
        "Два вещественных числа: минимальное, затем максимальное.",
        "8\n3\n5\n2", ["8\n3\n5\n2", "1\n2\n3\n4", "4\n3\n2\n1", "-1\n0\n1\n-2", "5\n5\n5\n5", "10.5\n-2.5\n7.5\n0", "100\n20\n30\n40", "7\n7\n3\n9"],
        solve_proc_11,
    )
    spec(
        "proc", 12, "Сортировка по возрастанию",
        "Описать процедуру SortInc3(A, B, C), меняющую содержимое переменных "
        "A, B, C таким образом, чтобы их значения оказались упорядоченными "
        "по возрастанию. С помощью этой процедуры упорядочить по возрастанию "
        "два данных набора из трёх чисел: (A1, B1, C1) и (A2, B2, C2).",
        "Шесть вещественных чисел: сначала A1, B1, C1, затем A2, B2, C2.",
        "Шесть чисел: первый набор по возрастанию, затем второй.",
        "3\n1\n2\n6\n5\n4", ["3\n1\n2\n6\n5\n4", "1\n2\n3\n4\n5\n6", "9\n8\n7\n6\n5\n4", "-1\n0\n1\n2\n-2\n0", "5\n5\n5\n5\n5\n5", "1.5\n0.5\n2.5\n3.5\n1.5\n2.5", "10\n20\n30\n15\n25\n35", "7\n3\n9\n1\n8\n2"],
        solve_proc_12,
    )
    spec(
        "proc", 13, "Сортировка по убыванию",
        "Описать процедуру SortDec3(A, B, C), меняющую содержимое переменных "
        "A, B, C таким образом, чтобы их значения оказались упорядоченными "
        "по убыванию. С помощью этой процедуры упорядочить по убыванию "
        "два данных набора из трёх чисел: (A1, B1, C1) и (A2, B2, C2).",
        "Шесть вещественных чисел: сначала A1, B1, C1, затем A2, B2, C2.",
        "Шесть чисел: первый набор по убыванию, затем второй.",
        "3\n1\n2\n6\n5\n4", ["3\n1\n2\n6\n5\n4", "1\n2\n3\n4\n5\n6", "9\n8\n7\n6\n5\n4", "-1\n0\n1\n2\n-2\n0", "5\n5\n5\n5\n5\n5", "1.5\n0.5\n2.5\n3.5\n1.5\n2.5", "10\n20\n30\n15\n25\n35", "7\n3\n9\n1\n8\n2"],
        solve_proc_13,
    )
    spec(
        "proc", 14, "Правый циклический сдвиг",
        "Описать процедуру ShiftRight3(A, B, C), выполняющую правый "
        "циклический сдвиг: значение A переходит в B, значение B — в C, "
        "значение C — в A. С помощью этой процедуры выполнить правый "
        "циклический сдвиг для двух данных наборов из трёх чисел: "
        "(A1, B1, C1) и (A2, B2, C2).",
        "Шесть вещественных чисел: сначала A1, B1, C1, затем A2, B2, C2.",
        "Шесть чисел: первый набор после сдвига, затем второй.",
        "1\n2\n3\n4\n5\n6", ["1\n2\n3\n4\n5\n6", "10\n20\n30\n40\n50\n60", "-1\n-2\n-3\n-4\n-5\n-6", "0.5\n1.5\n2.5\n3.5\n4.5\n5.5", "5\n5\n5\n5\n5\n5", "1\n2\n3\n3\n2\n1", "7\n8\n9\n10\n11\n12", "0\n0\n1\n1\n0\n0"],
        solve_proc_14,
    )
    spec(
        "proc", 15, "Левый циклический сдвиг",
        "Описать процедуру ShiftLeft3(A, B, C), выполняющую левый циклический "
        "сдвиг: значение A переходит в C, значение C — в B, значение B — в A. "
        "С помощью этой процедуры выполнить левый циклический сдвиг для двух "
        "данных наборов из трёх чисел: (A1, B1, C1) и (A2, B2, C2).",
        "Шесть вещественных чисел: сначала A1, B1, C1, затем A2, B2, C2.",
        "Шесть чисел: первый набор после сдвига, затем второй.",
        "1\n2\n3\n4\n5\n6", ["1\n2\n3\n4\n5\n6", "10\n20\n30\n40\n50\n60", "-1\n-2\n-3\n-4\n-5\n-6", "0.5\n1.5\n2.5\n3.5\n4.5\n5.5", "5\n5\n5\n5\n5\n5", "1\n2\n3\n3\n2\n1", "7\n8\n9\n10\n11\n12", "0\n0\n1\n1\n0\n0"],
        solve_proc_15,
    )
    spec(
        "proc", 16, "Функция Sign",
        "Описать функцию Sign(X) целого типа, возвращающую для вещественного "
        "числа X следующие значения: −1, если X < 0; 0, если X = 0; 1, если X > 0. "
        "С помощью этой функции найти значение выражения Sign(A) + Sign(B) "
        "для данных вещественных чисел A и B.",
        "Два вещественных числа A и B, каждое на новой строке.",
        "Одно целое число — Sign(A) + Sign(B).",
        "-5\n3", ["-5\n3", "0\n0", "2.5\n-0.5", "10\n20", "-3\n-7", "0\n5", "-1\n1", "100\n-100"],
        solve_proc_16,
    )
    spec(
        "proc", 17, "Количество корней",
        "Описать функцию RootCount(A, B, C) целого типа, определяющую "
        "количество корней квадратного уравнения A·x² + B·x + C = 0 "
        "(A, B, C — вещественные параметры, A ≠ 0). С её помощью найти "
        "количество корней для каждого из трёх квадратных уравнений "
        "с данными коэффициентами. Количество корней определять по значению "
        "дискриминанта D = B² − 4·A·C.",
        "Девять вещественных чисел: для каждого из трёх уравнений — A, B, C.",
        "Три целых числа — количество корней каждого уравнения.",
        "1\n-3\n2\n1\n2\n1\n1\n0\n1",
        ["1\n-3\n2\n1\n2\n1\n1\n0\n1", "1\n0\n1\n1\n-2\n1\n1\n2\n1", "1\n0\n-4\n1\n0\n0\n1\n0\n9", "2\n-4\n2\n1\n-5\n6\n1\n1\n1", "1\n-1\n-6\n1\n4\n4\n1\n-6\n9", "3\n2\n-1\n1\n-2\n3\n2\n3\n1", "1\n-10\n25\n1\n10\n25\n1\n0\n-9", "1\n-7\n12\n1\n-8\n15\n1\n-9\n20"],
        solve_proc_17,
    )
    spec(
        "proc", 18, "Площадь круга",
        "Описать функцию CircleS(R) вещественного типа, находящую площадь "
        "круга радиуса R. С помощью этой функции найти площади трёх кругов "
        "с данными радиусами. Площадь круга радиуса R вычисляется по формуле "
        "S = π·R². В качестве значения π использовать 3.14.",
        "Три положительных вещественных числа — радиусы, каждое на новой строке.",
        "Три вещественных числа — площади кругов.",
        "1\n2\n3", ["1\n2\n3", "0.5\n1.5\n2.5", "10\n20\n30", "0.1\n0.2\n0.3", "5\n5\n5", "1.25\n2.25\n3.25", "100\n50\n25", "7\n8\n9"],
        solve_proc_18,
    )
    spec(
        "proc", 19, "Площадь кольца",
        "Описать функцию RingS(R1, R2) вещественного типа, находящую площадь "
        "кольца, заключённого между двумя окружностями с общим центром "
        "и радиусами R1 и R2 (R1 > R2). С её помощью найти площади трёх колец, "
        "для которых даны внешние и внутренние радиусы. Воспользоваться "
        "формулой площади круга радиуса R: S = π·R². В качестве значения π "
        "использовать 3.14.",
        "Шесть положительных вещественных чисел: для каждого кольца — R1, R2.",
        "Три вещественных числа — площади колец.",
        "5\n3\n10\n6\n7\n2", ["5\n3\n10\n6\n7\n2", "1\n0.5\n2\n1\n3\n2.5", "10\n9\n20\n10\n30\n20", "100\n99\n50\n49\n10\n9", "4\n3\n8\n6\n12\n9", "2.5\n1.5\n3.5\n2.5\n4.5\n3.5", "7\n6\n8\n7\n9\n8", "6\n2\n9\n3\n12\n4"],
        solve_proc_19,
    )
    spec(
        "proc", 20, "Периметр равнобедренного треугольника",
        "Описать функцию TriangleP(a, h), находящую периметр равнобедренного "
        "треугольника по его основанию a и высоте h, проведённой к основанию. "
        "С помощью этой функции найти периметры трёх треугольников, для которых "
        "даны основания и высоты. Для нахождения боковой стороны b треугольника "
        "использовать теорему Пифагора: b² = (a/2)² + h².",
        "Шесть положительных вещественных чисел: для каждого треугольника — a, h.",
        "Три вещественных числа — периметры.",
        "6\n4\n8\n3\n10\n12", ["6\n4\n8\n3\n10\n12", "2\n1\n4\n2\n6\n3", "10\n5\n20\n10\n30\n15", "1\n1\n2\n2\n3\n3", "3\n4\n5\n12\n8\n6", "7\n24\n10\n24\n9\n40", "2.5\n1.5\n3.5\n2.5\n4.5\n3.5", "100\n50\n60\n30\n80\n40"],
        solve_proc_20,
    )


def build_series() -> None:
    spec(
        "series", 1, "Сумма десяти чисел",
        "Даны десять вещественных чисел. Найти их сумму.",
        "Десять вещественных чисел в одной строке через пробел.",
        "Одно вещественное число — сумма.",
        "1 2 3 4 5 6 7 8 9 10", ["1 2 3 4 5 6 7 8 9 10", "0 0 0 0 0 0 0 0 0 0", "-1 -2 -3 -4 -5 1 2 3 4 5", "0.5 1.5 2.5 3.5 4.5 5.5 6.5 7.5 8.5 9.5", "10 20 30 40 50 60 70 80 90 100", "1.1 2.2 3.3 4.4 5.5 6.6 7.7 8.8 9.9 10.1", "-1 -1 -1 -1 -1 -1 -1 -1 -1 -1", "100 200 300 400 500 600 700 800 900 1000"],
        solve_series_1,
    )
    spec(
        "series", 2, "Произведение десяти чисел",
        "Даны десять вещественных чисел. Найти их произведение.",
        "Десять вещественных чисел в одной строке через пробел.",
        "Одно вещественное число — произведение.",
        "1 2 3 4 5 6 7 8 9 10", ["1 2 3 4 5 6 7 8 9 10", "1 1 1 1 1 1 1 1 1 1", "-1 -1 -1 -1 -1 1 1 1 1 1", "0.5 1.5 2.5 3.5 4.5 5.5 6.5 7.5 8.5 9.5", "2 2 2 2 2 2 2 2 2 2", "1.1 2.2 3.3 4.4 5.5 6.6 7.7 8.8 9.9 10.1", "-2 -2 -2 -2 -2 -2 -2 -2 -2 -2", "0 1 2 3 4 5 6 7 8 9"],
        solve_series_2,
    )
    spec(
        "series", 3, "Среднее арифметическое десяти чисел",
        "Даны десять вещественных чисел. Найти их среднее арифметическое.",
        "Десять вещественных чисел в одной строке через пробел.",
        "Одно вещественное число — среднее арифметическое.",
        "1 2 3 4 5 6 7 8 9 10", ["1 2 3 4 5 6 7 8 9 10", "0 0 0 0 0 0 0 0 0 0", "-1 -2 -3 -4 -5 1 2 3 4 5", "0.5 1.5 2.5 3.5 4.5 5.5 6.5 7.5 8.5 9.5", "10 20 30 40 50 60 70 80 90 100", "1.1 2.2 3.3 4.4 5.5 6.6 7.7 8.8 9.9 10.1", "-1 -1 -1 -1 -1 -1 -1 -1 -1 -1", "100 200 300 400 500 600 700 800 900 1000"],
        solve_series_3,
    )
    spec(
        "series", 4, "Сумма и произведение набора",
        "Дано целое число N и набор из N вещественных чисел. Вывести сумму "
        "и произведение чисел из данного набора.",
        "Сначала N, затем N вещественных чисел в одной строке через пробел.",
        "Два вещественных числа: сумма, затем произведение.",
        "3\n2 3 4", ["3\n2 3 4", "1\n5", "5\n1 2 3 4 5", "4\n-1 -2 -3 -4", "2\n0.5 2", "6\n1 1 1 1 1 1", "5\n0 1 2 3 4", "4\n10 20 30 40"],
        solve_series_4,
    )
    spec(
        "series", 5, "Целые части",
        "Дано целое число N и набор из N положительных вещественных чисел. "
        "Вывести в том же порядке целые части всех чисел из данного набора "
        "(как вещественные числа с нулевой дробной частью), а также сумму "
        "всех целых частей.",
        "Сначала N, затем N положительных вещественных чисел в одной строке через пробел.",
        "N целых частей, затем их сумма.",
        "3\n1.5 2.7 3.9", ["3\n1.5 2.7 3.9", "1\n5.6", "5\n1.1 2.2 3.3 4.4 5.5", "4\n10.9 20.1 30.4 40.0", "2\n0.5 0.9", "6\n1 2 3 4 5 6", "3\n100.99 200.01 300.4", "5\n1.25 2.5 3.75 4.0 5.5"],
        solve_series_5,
    )
    spec(
        "series", 6, "Дробные части",
        "Дано целое число N и набор из N положительных вещественных чисел. "
        "Вывести в том же порядке дробные части всех чисел из данного набора "
        "(как вещественные числа с нулевой целой частью), а также произведение "
        "всех дробных частей.",
        "Сначала N, затем N положительных вещественных чисел в одной строке через пробел.",
        "N дробных частей, затем их произведение.",
        "3\n1.5 2.7 3.9", ["3\n1.5 2.7 3.9", "1\n5.6", "5\n1.1 2.2 3.3 4.4 5.5", "4\n10.9 20.1 30.4 40.0", "2\n0.5 0.9", "6\n1.25 2.25 3.25 4.25 5.25 6.25", "3\n100.99 200.01 300.4", "5\n1.25 2.5 3.75 4.0 5.5"],
        solve_series_6,
    )
    spec(
        "series", 7, "Округлённые значения",
        "Дано целое число N и набор из N вещественных чисел. Вывести в том же "
        "порядке округлённые значения всех чисел из данного набора (как целые "
        "числа), а также сумму всех округлённых значений.",
        "Сначала N, затем N вещественных чисел в одной строке через пробел.",
        "N округлённых значений, затем их сумма.",
        "3\n1.4 2.6 -3.2", ["3\n1.4 2.6 -3.2", "1\n5.6", "5\n1.1 2.2 3.3 4.4 5.6", "4\n10.9 20.1 30.4 40.0", "2\n0.4 0.6", "6\n1 2 3 4 5 6", "3\n100.99 200.01 300.4", "5\n-1.4 -2.6 3.2 4.8 -5.1"],
        solve_series_7,
    )
    spec(
        "series", 8, "Чётные числа",
        "Дано целое число N и набор из N целых чисел. Вывести в том же порядке "
        "все чётные числа из данного набора и количество K таких чисел.",
        "Сначала N, затем N целых чисел в одной строке через пробел.",
        "Чётные числа в исходном порядке, затем их количество.",
        "5\n1 2 3 4 5", ["5\n1 2 3 4 5", "4\n2 4 6 8", "4\n1 3 5 7", "6\n-2 -1 0 1 2 3", "1\n10", "5\n0 0 0 0 0", "7\n11 12 13 14 15 16 17", "5\n-4 -3 -2 -1 0"],
        solve_series_8,
    )
    spec(
        "series", 9, "Номера нечётных",
        "Дано целое число N и набор из N целых чисел. Вывести в том же порядке "
        "номера всех нечётных чисел из данного набора и количество K таких чисел.",
        "Сначала N, затем N целых чисел в одной строке через пробел.",
        "Номера нечётных чисел (с 1), затем их количество.",
        "5\n1 2 3 4 5", ["5\n1 2 3 4 5", "4\n2 4 6 8", "4\n1 3 5 7", "6\n-2 -1 0 1 2 3", "1\n7", "5\n0 0 0 0 0", "7\n11 12 13 14 15 16 17", "5\n-4 -3 -2 -1 0"],
        solve_series_9,
    )
    spec(
        "series", 10, "Есть положительные?",
        "Дано целое число N и набор из N целых чисел. Если в наборе имеются "
        "положительные числа, то вывести True; в противном случае вывести False.",
        "Сначала N, затем N целых чисел в одной строке через пробел.",
        "True или False.",
        "5\n1 -2 0 4 -5", ["5\n1 -2 0 4 -5", "3\n-1 -2 -3", "4\n0 0 0 0", "1\n5", "6\n-1 0 -2 0 -3 0", "3\n10 20 30", "4\n-10 -20 -30 -40", "2\n0 -1"],
        solve_series_10,
    )
    spec(
        "series", 11, "Есть числа меньше K?",
        "Даны целые числа K, N и набор из N целых чисел. Если в наборе имеются "
        "числа, меньшие K, то вывести True; в противном случае вывести False.",
        "Сначала K и N, затем N целых чисел.",
        "True или False.",
        "5\n4\n1 2 3 4", ["5\n4\n1 2 3 4", "0\n3\n1 2 3", "10\n4\n10 20 30 40", "-5\n3\n-1 -2 -3", "5\n5\n5 6 7 8 9", "5\n2\n10 20", "0\n3\n0 1 2", "7\n4\n6 7 8 9"],
        solve_series_11,
    )
    spec(
        "series", 12, "Количество чисел до нуля",
        "Дан набор ненулевых целых чисел; признак его завершения — число 0. "
        "Вывести количество чисел в наборе.",
        "Ненулевые целые числа в одной строке через пробел, в конце 0.",
        "Одно целое число — количество чисел до нуля.",
        "1 2 3 0", ["1 2 3 0", "0", "5 0", "1 -2 3 -4 5 0", "10 20 30 40 50 60 70 80 90 100 0", "-1 -2 -3 0", "7 7 7 0", "0 1 2 3"],
        solve_series_12,
    )
    spec(
        "series", 13, "Сумма положительных чётных",
        "Дан набор ненулевых целых чисел; признак его завершения — число 0. "
        "Вывести сумму всех положительных чётных чисел из данного набора. "
        "Если требуемые числа в наборе отсутствуют, то вывести 0.",
        "Ненулевые целые числа в одной строке через пробел, в конце 0.",
        "Одно целое число — сумма.",
        "1 2 3 4 5 0", ["1 2 3 4 5 0", "0", "2 4 6 8 0", "1 3 5 7 0", "-2 -4 2 4 0", "10 -10 20 -20 0", "0 2 4", "3 6 9 12 15 0"],
        solve_series_13,
    )
    spec(
        "series", 14, "Меньше K",
        "Дано целое число K и набор ненулевых целых чисел; признак его "
        "завершения — число 0. Вывести количество чисел в наборе, меньших K.",
        "Сначала K, затем ненулевые целые числа в одной строке через пробел и 0 в конце.",
        "Одно целое число — количество чисел, меньших K.",
        "5\n1 2 3 4 5 6 0", ["5\n1 2 3 4 5 6 0", "0\n-1 -2 -3 0", "10\n10 20 30 0", "5\n6 7 8 0", "5\n4 5 6 0", "-5\n-10 -3 0", "100\n1 2 3 0", "2\n1 2 3 0"],
        solve_series_14,
    )
    spec(
        "series", 15, "Первый больше K",
        "Дано целое число K и набор ненулевых целых чисел; признак его "
        "завершения — число 0. Вывести номер первого числа в наборе, большего K. "
        "Если таких чисел нет, то вывести 0.",
        "Сначала K, затем ненулевые целые числа в одной строке через пробел и 0 в конце.",
        "Одно целое число — номер (с 1) или 0.",
        "5\n1 6 7 8 0", ["5\n1 6 7 8 0", "5\n1 2 3 4 0", "0\n1 2 3 0", "10\n5 15 25 0", "-5\n-10 -6 0", "5\n6 7 8 0", "5\n4 6 7 0", "100\n101 102 103 0"],
        solve_series_15,
    )
    spec(
        "series", 16, "Последний больше K",
        "Дано целое число K и набор ненулевых целых чисел; признак его "
        "завершения — число 0. Вывести номер последнего числа в наборе, "
        "большего K. Если таких чисел нет, то вывести 0.",
        "Сначала K, затем ненулевые целые числа в одной строке через пробел и 0 в конце.",
        "Одно целое число — номер (с 1) или 0.",
        "5\n1 6 7 8 0", ["5\n1 6 7 8 0", "5\n1 2 3 4 0", "0\n1 2 3 0", "10\n5 15 25 0", "-5\n-10 -6 0", "5\n6 7 8 0", "5\n4 6 7 0", "100\n101 102 103 0"],
        solve_series_16,
    )
    spec(
        "series", 17, "Вставка B",
        "Дано вещественное число B, целое число N и набор из N вещественных "
        "чисел, упорядоченных по возрастанию. Вывести элементы набора вместе "
        "с числом B, сохраняя упорядоченность выводимых чисел.",
        "Сначала B и N, затем N вещественных чисел по возрастанию в одной строке.",
        "N + 1 число в порядке возрастания.",
        "3.5 5\n1 2 4 6 7", ["3.5 5\n1 2 4 6 7", "0 3\n1 2 3", "10 3\n1 2 3", "5 4\n1 2 3 4", "2.5 4\n1 2 3 4", "-1 4\n0 1 2 3", "100 5\n10 20 30 40 50", "5 1\n5"],
        solve_series_17,
    )
    spec(
        "series", 18, "Различные элементы",
        "Дано целое число N и набор из N целых чисел, упорядоченный "
        "по возрастанию. Данный набор может содержать одинаковые элементы. "
        "Вывести в том же порядке все различные элементы данного набора.",
        "Сначала N, затем N целых чисел по возрастанию в одной строке.",
        "Различные числа в порядке возрастания.",
        "6\n1 1 2 3 3 5", ["6\n1 1 2 3 3 5", "3\n1 2 3", "5\n7 7 7 7 7", "4\n-2 -2 0 0", "7\n1 2 2 2 3 4 4", "1\n10", "8\n1 1 1 2 2 3 3 3", "5\n-5 -4 -4 -3 -3"],
        solve_series_18,
    )
    spec(
        "series", 19, "Меньше левого соседа",
        "Дано целое число N (> 1) и набор из N целых чисел. Вывести те элементы "
        "в наборе, которые меньше своего левого соседа, и количество K таких "
        "элементов.",
        "Сначала N, затем N целых чисел в одной строке через пробел.",
        "Найденные элементы в порядке следования, затем их количество.",
        "5\n5 3 4 2 6", ["5\n5 3 4 2 6", "4\n1 2 3 4", "4\n4 3 2 1", "6\n10 1 9 2 8 3", "2\n5 4", "5\n5 5 5 5 5", "7\n7 6 5 4 3 2 1", "6\n-1 -2 0 -3 5 -4"],
        solve_series_19,
    )
    spec(
        "series", 20, "Меньше правого соседа",
        "Дано целое число N (> 1) и набор из N целых чисел. Вывести те элементы "
        "в наборе, которые меньше своего правого соседа, и количество K таких "
        "элементов.",
        "Сначала N, затем N целых чисел в одной строке через пробел.",
        "Найденные элементы в порядке следования, затем их количество.",
        "5\n5 3 4 2 6", ["5\n5 3 4 2 6", "4\n1 2 3 4", "4\n4 3 2 1", "6\n10 1 9 2 8 3", "2\n5 4", "5\n5 5 5 5 5", "7\n7 6 5 4 3 2 1", "6\n-1 -2 0 -3 5 -4"],
        solve_series_20,
    )


if __name__ == "__main__":
    main()
