from math import ceil


class Paginator:
    def __init__(self, total: int, per_page: int):
        self.total = total
        self.per_page = per_page
        self.num_pages = max(1, ceil(total / per_page))
        self.page_range = range(1, self.num_pages + 1)


class Page:
    def __init__(self, items: list, number: int, paginator: Paginator):
        self.items = items
        self.number = number
        self.paginator = paginator

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    @property
    def has_other_pages(self) -> bool:
        return self.paginator.num_pages > 1

    @property
    def has_previous(self) -> bool:
        return self.number > 1

    @property
    def has_next(self) -> bool:
        return self.number < self.paginator.num_pages

    @property
    def previous_page_number(self) -> int:
        return max(1, self.number - 1)

    @property
    def next_page_number(self) -> int:
        return min(self.paginator.num_pages, self.number + 1)


def paginate(items: list, page: int, per_page: int) -> Page:
    paginator = Paginator(len(items), per_page)
    page = max(1, min(page, paginator.num_pages))
    start = (page - 1) * per_page
    end = start + per_page
    return Page(items[start:end], page, paginator)
