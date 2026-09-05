from dashboard.data import PAGE_SIZE, fetch_funnel_records


class _FakeResponse:
    def __init__(self, data: list[dict]):
        self.data = data


class _FakeQuery:
    def __init__(self, all_rows: list[dict]):
        self._all_rows = all_rows
        self._start = 0
        self._end = None

    def select(self, *_args, **_kwargs) -> "_FakeQuery":
        return self

    def range(self, start: int, end: int) -> "_FakeQuery":
        self._start = start
        self._end = end
        return self

    def execute(self) -> _FakeResponse:
        return _FakeResponse(self._all_rows[self._start : self._end + 1])


class _FakeClient:
    def __init__(self, all_rows: list[dict]):
        self._all_rows = all_rows

    def table(self, _name: str) -> _FakeQuery:
        return _FakeQuery(self._all_rows)


def _make_row(i: int) -> dict:
    return {"id": i, "created_at": "2026-01-01T00:00:00Z", "ad_budget": 1000 + i, "closed": i}


def test_fetch_funnel_records_drops_db_only_columns() -> None:
    client = _FakeClient([_make_row(1), _make_row(2)])

    df = fetch_funnel_records(client)

    assert "id" not in df.columns
    assert "created_at" not in df.columns
    assert list(df["ad_budget"]) == [1001, 1002]


def test_fetch_funnel_records_paginates_past_page_size() -> None:
    all_rows = [_make_row(i) for i in range(PAGE_SIZE + 50)]
    client = _FakeClient(all_rows)

    df = fetch_funnel_records(client)

    assert len(df) == PAGE_SIZE + 50
