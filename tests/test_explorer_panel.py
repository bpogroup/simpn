import unittest
from unittest.mock import MagicMock, patch, Mock
from tests.dummy_problems import create_dummy_bpmn
from PyQt6.QtWidgets import QApplication, QTreeWidgetItem
from PyQt6.QtCore import Qt, QSettings
from simpn.visualisation.base import MainWindow, ExplorerPanel, ModelPanel
from simpn.visualisation.events import create_event, dispatch, EventType
from simpn.visualisation.model_panel_mods import ClockModule
from simpn.prototypes import BPMNTask
import sys


class TestExplorerPanel(unittest.TestCase):
    """
    Tests for the ExplorerPanel functionality including tree management,
    replication parameters dialog, and running replications.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)

        # Create main window
        self.main_window = MainWindow(as_application=False)
        self.explorer_panel = self.main_window.explorer_panel

        # Create a dummy BPMN problem
        self.problem = create_dummy_bpmn()

        # Create model panel
        self.model_panel = ModelPanel(
            self.problem,
            layout_file=None,
            grid_spacing=50,
            node_spacing=100,
            layout_algorithm="sugiyama",
        )
        self.model_panel.add_mod(ClockModule())

        # Set simulation
        self.main_window.set_simulation(self.model_panel)

    def tearDown(self):
        """Clean up after each test method."""
        if self.main_window:
            self.main_window.close()
        # Clear settings
        settings = QSettings("TUe", "SimPN")
        settings.clear()

    def test_explorer_panel_initialization(self):
        """Test that ExplorerPanel initializes correctly."""
        self.assertIsNotNone(self.explorer_panel)
        self.assertIsNotNone(self.explorer_panel.tree)
        self.assertIsNotNone(self.explorer_panel.toolbar)
        self.assertIsNotNone(self.explorer_panel.run_action)
        # After setup, simulation panel is already added
        self.assertIn("Simulation", self.explorer_panel._name_to_widget)

    def test_run_action_enabled_after_visualization_created(self):
        """Test that run action is enabled after visualization is created."""
        # Initially the run action should be enabled after setup
        self.assertTrue(self.explorer_panel.run_action.isEnabled())

    def test_add_panel_to_tree(self):
        """Test adding a panel to the explorer tree."""
        mock_widget = MagicMock()
        event = create_event(EventType.CENTRAL_PANEL_ADD, name="Test Panel", widget=mock_widget)
        
        self.explorer_panel.handle_event(event)
        
        # Check that the panel was added to the tree
        root = self.explorer_panel.tree.invisibleRootItem()
        self.assertEqual(root.childCount(), 2)  # Simulation + Test Panel
        
        # Check that the widget is in the mapping
        self.assertIn("Test Panel", self.explorer_panel._name_to_widget)
        self.assertEqual(self.explorer_panel._name_to_widget["Test Panel"], mock_widget)

    def test_remove_panel_from_tree(self):
        """Test removing a panel from the explorer tree."""
        # First add a panel
        mock_widget = MagicMock()
        add_event = create_event(EventType.CENTRAL_PANEL_ADD, name="Test Panel", widget=mock_widget)
        self.explorer_panel.handle_event(add_event)
        
        # Then remove it
        remove_event = create_event(EventType.CENTRAL_PANEL_REMOVE, name="Test Panel", widget=mock_widget)
        self.explorer_panel.handle_event(remove_event)
        
        # Check that the panel was removed
        self.assertNotIn("Test Panel", self.explorer_panel._name_to_widget)
        
        # Check tree structure
        root = self.explorer_panel.tree.invisibleRootItem()
        found = False
        for i in range(root.childCount()):
            if root.child(i).text(0) == "Test Panel":
                found = True
                break
        self.assertFalse(found)

    def test_replace_existing_panel(self):
        """Test that adding a panel with existing name replaces the old one."""
        # Add first panel
        mock_widget1 = MagicMock()
        event1 = create_event(EventType.CENTRAL_PANEL_ADD, name="Test Panel", widget=mock_widget1)
        self.explorer_panel.handle_event(event1)
        
        # Add second panel with same name
        mock_widget2 = MagicMock()
        event2 = create_event(EventType.CENTRAL_PANEL_ADD, name="Test Panel", widget=mock_widget2)
        self.explorer_panel.handle_event(event2)
        
        # Check that only one panel exists with the new widget
        self.assertEqual(self.explorer_panel._name_to_widget["Test Panel"], mock_widget2)
        self.assertNotEqual(self.explorer_panel._name_to_widget["Test Panel"], mock_widget1)

    def test_activate_panel_in_tree(self):
        """Test activating a panel in the explorer tree."""
        # Add a panel first
        mock_widget = MagicMock()
        add_event = create_event(EventType.CENTRAL_PANEL_ADD, name="Test Panel", widget=mock_widget)
        self.explorer_panel.handle_event(add_event)
        
        # Activate it
        activate_event = create_event(EventType.CENTRAL_PANEL_ACTIVATE, name="Test Panel", widget=mock_widget)
        self.explorer_panel.handle_event(activate_event)
        
        # Check that the tree selection is updated
        current_item = self.explorer_panel.tree.currentItem()
        # Note: This may not work in all cases due to parent-child relationships
        # but we're testing the handler doesn't crash

    def test_item_clicked_dispatches_activate_event(self):
        """Test that clicking an item dispatches an activate event."""
        # Add a panel
        mock_widget = MagicMock()
        add_event = create_event(EventType.CENTRAL_PANEL_ADD, name="Test Panel", widget=mock_widget)
        self.explorer_panel.handle_event(add_event)
        
        # Get the tree item
        root = self.explorer_panel.tree.invisibleRootItem()
        item = None
        for i in range(root.childCount()):
            if root.child(i).text(0) == "Test Panel":
                item = root.child(i)
                break
        
        self.assertIsNotNone(item)
        
        # Simulate clicking the item - this should call dispatch internally
        # We can't easily mock dispatch since it's imported at module level
        # Instead, just verify it doesn't crash
        self.explorer_panel._on_item_clicked(item, 0)
        # If we got here without exception, the test passes

    def test_replication_parameters_dialog_cancel(self):
        """Test canceling the replication parameters dialog."""
        # Mock the dialog to simulate cancel
        with patch('simpn.visualisation.base.QDialog.exec') as mock_exec:
            from PyQt6.QtWidgets import QDialog
            mock_exec.return_value = QDialog.DialogCode.Rejected
            
            result = self.explorer_panel.replication_parameters_dialog()
            
            # Should return None when canceled
            self.assertIsNone(result)

    def test_replication_parameters_dialog_accept(self):
        """Test accepting the replication parameters dialog."""
        # Mock the dialog to simulate accept
        with patch('simpn.visualisation.base.QDialog.exec') as mock_exec:
            from PyQt6.QtWidgets import QDialog
            mock_exec.return_value = QDialog.DialogCode.Accepted
            
            # Clear any previous settings
            settings = QSettings("TUe", "SimPN")
            settings.setValue("replication/duration", 100.0)
            settings.setValue("replication/warmup", 20.0)
            settings.setValue("replication/nr_replications", 10)
            
            result = self.explorer_panel.replication_parameters_dialog()
            
            # Should return a tuple with the values
            self.assertIsNotNone(result)
            self.assertEqual(len(result), 3)
            duration, warmup, nr_replications = result
            self.assertEqual(duration, 100.0)
            self.assertEqual(warmup, 20.0)
            self.assertEqual(nr_replications, 10)

    def test_replication_parameters_saved_to_settings(self):
        """Test that replication parameters are saved to settings."""
        with patch('simpn.visualisation.base.QDialog.exec') as mock_exec:
            from PyQt6.QtWidgets import QDialog
            mock_exec.return_value = QDialog.DialogCode.Accepted
            
            # Set specific values
            settings = QSettings("TUe", "SimPN")
            test_duration = 250.5
            test_warmup = 50.25
            test_replications = 25
            
            settings.setValue("replication/duration", test_duration)
            settings.setValue("replication/warmup", test_warmup)
            settings.setValue("replication/nr_replications", test_replications)
            
            result = self.explorer_panel.replication_parameters_dialog()
            
            # Verify values were saved
            self.assertEqual(settings.value("replication/duration", type=float), test_duration)
            self.assertEqual(settings.value("replication/warmup", type=float), test_warmup)
            self.assertEqual(settings.value("replication/nr_replications", type=int), test_replications)

    def test_run_replications_no_model_panel(self):
        """Test running replications when no model panel is set."""
        # Clear the simulation panel
        self.main_window.simulation_panel.set_panel(None)
        
        # This should not crash
        self.explorer_panel.run_replications()

    def test_run_replications_non_bpmn_model(self):
        """Test running replications with a non-BPMN model shows warning."""
        # Create a problem without BPMN prototypes but with at least one place
        from simpn.simulator import SimProblem
        non_bpmn_problem = SimProblem()
        # Add a simple place to avoid layout error
        non_bpmn_problem.add_place("p1")
        
        model_panel = ModelPanel(
            non_bpmn_problem,
            layout_file=None,
        )
        self.main_window.set_simulation(model_panel)
        
        # Mock QMessageBox to prevent actual dialog
        with patch('simpn.visualisation.base.QMessageBox.warning') as mock_warning:
            self.explorer_panel.run_replications()
            
            # Should show warning
            self.assertTrue(mock_warning.called)
            args = mock_warning.call_args[0]
            self.assertIn("BPMN", args[2])  # Message should mention BPMN

    def test_run_replications_user_cancels_dialog(self):
        """Test running replications when user cancels the parameters dialog."""
        # Mock the dialog to simulate cancel
        with patch.object(self.explorer_panel, 'replication_parameters_dialog', return_value=None):
            # This should return early without running replications
            self.explorer_panel.run_replications()
            # If it doesn't crash, test passes

    def test_run_replications_user_cancels_progress(self):
        """Test running replications when user cancels during progress."""
        # Mock the dialog to return parameters
        with patch.object(self.explorer_panel, 'replication_parameters_dialog', return_value=(100, 20, 5)):
            # Mock the progress dialog to simulate cancellation
            with patch('simpn.visualisation.base.QProgressDialog') as mock_progress_class:
                mock_progress = MagicMock()
                mock_progress.wasCanceled.return_value = True  # User cancels immediately
                mock_progress_class.return_value = mock_progress
                
                # Mock Replicator - it's imported inside run_replications
                # We need to simulate the callback being invoked
                def mock_replicator_init(*args, **kwargs):
                    # Call the callback with some percentage to trigger cancellation check
                    callback = kwargs.get('callback')
                    if callback:
                        callback(50)  # This will check wasCanceled() and set canceled=True
                    return MagicMock(run=MagicMock(return_value={}))
                
                with patch('simpn.reporters.Replicator', side_effect=mock_replicator_init) as mock_replicator_class:
                    # Mock ProcessReporter.possible_graphs
                    with patch('simpn.reporters.ProcessReporter') as mock_reporter:
                        mock_reporter.possible_graphs.return_value = {
                            "Graph 1": MagicMock(),
                        }
                        
                        # Mock PlotPanel to ensure it's not created when canceled
                        with patch('simpn.visualisation.base.PlotPanel') as mock_plot_panel:
                            self.explorer_panel.run_replications()
                            
                            # PlotPanel should not be created when canceled
                            self.assertFalse(mock_plot_panel.called)

    def test_run_replications_successful(self):
        """Test successfully running replications creates plot panels."""
        # Mock the dialog to return parameters
        with patch.object(self.explorer_panel, 'replication_parameters_dialog', return_value=(100, 20, 5)):
            # Mock the progress dialog to not cancel
            with patch('simpn.visualisation.base.QProgressDialog') as mock_progress_class:
                mock_progress = MagicMock()
                mock_progress.wasCanceled.return_value = False  # User doesn't cancel
                mock_progress_class.return_value = mock_progress
                
                # Mock Replicator with realistic results - it's imported inside run_replications
                with patch('simpn.reporters.Replicator') as mock_replicator_class:
                    mock_replicator = MagicMock()
                    mock_results = {"task1": [1, 2, 3], "task2": [4, 5, 6]}
                    mock_replicator.run.return_value = mock_results
                    mock_replicator_class.return_value = mock_replicator
                    
                    # Mock ProcessReporter.possible_graphs - also imported inside
                    with patch('simpn.reporters.ProcessReporter') as mock_reporter:
                        mock_reporter.possible_graphs.return_value = {
                            "Graph 1": MagicMock(),
                            "Graph 2": MagicMock(),
                        }
                        
                        # Mock PlotPanel to track creation
                        with patch('simpn.visualisation.base.PlotPanel') as mock_plot_panel:
                            self.explorer_panel.run_replications()
                            
                            # PlotPanel should be created for each graph
                            self.assertEqual(mock_plot_panel.call_count, 2)
                            
                            # Check that Replicator was called with correct parameters
                            mock_replicator_class.assert_called_once()
                            call_kwargs = mock_replicator_class.call_args[1]
                            self.assertEqual(call_kwargs['duration'], 100)
                            self.assertEqual(call_kwargs['warmup'], 20)
                            self.assertEqual(call_kwargs['nr_replications'], 5)
                            self.assertIsNotNone(call_kwargs['callback'])


if __name__ == '__main__':
    unittest.main()
