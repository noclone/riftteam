from sqlalchemy import Column, Integer, String, select
from sqlalchemy.orm import DeclarativeBase

from app.services.query_helpers import apply_rank_filters


class Base(DeclarativeBase):
    pass


class FakeModel(Base):
    __tablename__ = "fake"
    id = Column(Integer, primary_key=True)
    tier = Column(String)


class TestApplyRankFilters:
    def test_no_filters_returns_unchanged(self):
        stmt = select(FakeModel)
        count_stmt = select(FakeModel.id)
        new_stmt, new_count = apply_rank_filters(stmt, count_stmt, None, None, FakeModel.tier)
        assert str(new_stmt) == str(stmt)
        assert str(new_count) == str(count_stmt)

    def test_min_rank_filters(self):
        stmt = select(FakeModel)
        count_stmt = select(FakeModel.id)
        new_stmt, new_count = apply_rank_filters(stmt, count_stmt, "GOLD", None, FakeModel.tier)
        compiled = str(new_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "fake.tier IN" in compiled

    def test_max_rank_filters(self):
        stmt = select(FakeModel)
        count_stmt = select(FakeModel.id)
        new_stmt, new_count = apply_rank_filters(stmt, count_stmt, None, "DIAMOND", FakeModel.tier)
        compiled = str(new_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "fake.tier IN" in compiled

    def test_both_filters(self):
        stmt = select(FakeModel)
        count_stmt = select(FakeModel.id)
        new_stmt, _ = apply_rank_filters(stmt, count_stmt, "GOLD", "DIAMOND", FakeModel.tier)
        compiled = str(new_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert compiled.count("fake.tier IN") == 2

    def test_allow_null(self):
        stmt = select(FakeModel)
        count_stmt = select(FakeModel.id)
        new_stmt, _ = apply_rank_filters(stmt, count_stmt, "GOLD", None, FakeModel.tier, allow_null=True)
        compiled = str(new_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "IS NULL" in compiled

    def test_invalid_rank_ignored(self):
        stmt = select(FakeModel)
        count_stmt = select(FakeModel.id)
        new_stmt, new_count = apply_rank_filters(stmt, count_stmt, "INVALID", "NOTREAL", FakeModel.tier)
        assert str(new_stmt) == str(stmt)
