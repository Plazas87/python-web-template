import pytest

from {{ package_name }}.domain.model.pagination import Page, PageRequest


def test_offset_is_zero_indexed_from_page_1() -> None:
    assert PageRequest(page=1, page_size=20).offset == 0
    assert PageRequest(page=2, page_size=20).offset == 20
    assert PageRequest(page=3, page_size=10).offset == 20


def test_page_rejects_page_below_one() -> None:
    with pytest.raises(ValueError):
        PageRequest(page=0)


def test_page_rejects_page_size_out_of_bounds() -> None:
    with pytest.raises(ValueError):
        PageRequest(page_size=0)
    with pytest.raises(ValueError):
        PageRequest(page_size=101)


def test_total_pages_rounds_up() -> None:
    assert Page(items=[], page=1, page_size=20, total=41).total_pages == 3
    assert Page(items=[], page=1, page_size=20, total=40).total_pages == 2
    assert Page(items=[], page=1, page_size=20, total=0).total_pages == 0
