import pytest
from unittest.mock import patch, MagicMock
from core.db import record_ingestion, has_been_processed, get_ingestion_stats

@patch('core.db.supabase')
def test_record_ingestion_success(mock_supabase):
    """Test that record_ingestion calls the Supabase insert method correctly."""
    # Setup mock chain: supabase.table().insert().execute()
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()
    
    mock_supabase.table.return_value = mock_table
    mock_table.insert.return_value = mock_insert
    mock_execute.data = [{"id": 99}]
    mock_insert.execute.return_value = mock_execute
    
    result_id = record_ingestion("youtube", "http://test.url", "Test Title")
    
    # Assertions
    assert result_id == 99
    mock_supabase.table.assert_called_with("ingestions")
    mock_table.insert.assert_called_once()
    
    # Check inserted data payload
    inserted_data = mock_table.insert.call_args[0][0]
    assert inserted_data["source_type"] == "youtube"
    assert inserted_data["source_url"] == "http://test.url"
    assert inserted_data["status"] == "success"

@patch('core.db.supabase')
def test_has_been_processed_true(mock_supabase):
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq1 = MagicMock()
    mock_eq2 = MagicMock()
    mock_execute = MagicMock()
    
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq1
    mock_eq1.eq.return_value = mock_eq2
    
    # Return 1 record meaning it exists
    mock_execute.data = [{"id": 1}]
    mock_eq2.execute.return_value = mock_execute
    
    assert has_been_processed("http://test.url") is True

@patch('core.db.supabase')
def test_has_been_processed_false(mock_supabase):
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq1 = MagicMock()
    mock_eq2 = MagicMock()
    mock_execute = MagicMock()
    
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq1
    mock_eq1.eq.return_value = mock_eq2
    
    # Return empty list meaning it does NOT exist
    mock_execute.data = []
    mock_eq2.execute.return_value = mock_execute
    
    assert has_been_processed("http://new.url") is False
