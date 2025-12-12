from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Callable, Optional

from simpn.simulator import SimProblem


class TimeUnit(Enum):
    """An enumeration for the unit in which simulation time is measured."""
    SECONDS = auto()
    """
    Measured in seconds.
    
    :meta hide-value:
    """
    MINUTES = auto()
    """
    Measured in minutes.

    :meta hide-value:
    """
    HOURS = auto()
    """
    Measured in hours.

    :meta hide-value:
    """
    DAYS = auto()
    """
    Measured in days.

    :meta hide-value:
    """


class Reporter:
    """
    A reporter can be passed to the simpn.simulator.SimProblem.simulate function to report on what happens during the simulator.
    To this end, a reported must implement the callback function.
    """
    def callback(self, timed_binding):
        """
        A function that is invoked by a simpn.simulator.SimProblem each time a event happened.
        It receives a timed_binding, which is a triple (binding, time, event):
        - binding = [(v1: SimVar, t1: SimToken), (v2: SimVar, t2: SimToken), ...] of the variable values that caused the event.
        - time is the simulation time at which the event happened.
        - event: SimEvent is the event that happened.

        :param timed_binding: the triple (binding, time, event) that described the event that happened with its variable values and the time at which it happened.
        """
        raise NotImplementedError


class SimpleReporter(Reporter):
    """
    A simple reporter that just prints the occurring events to the standard output.
    """
    def callback(self, timed_binding):
        result = str(timed_binding[2]) + "{"
        i = 0
        for var, token in timed_binding[0]:
            result += str(var) + ": " + str(token.value)
            if i < len(timed_binding[0])-1:
                result += ", "
            i += 1
        result += "}" + "@t=" + str(timed_binding[1])
        print(result)


class WarmupReporter(Reporter):
    """
    A reporter that reports on the warmup period of a simulation by computing the average cycle times over time.
    It assumes tasks are executed for cases that arrive via start_events and complete at end_events.
    """
    def __init__(self):
        self.times = [0]
        self.average_cycle_times = [0]

        self.__total_times = [0]
        self.__nr_completed_cases = 0
        self.__case_arrivals = {}

    def callback(self, timed_binding):
        (binding, time, event) = timed_binding
        if event.get_id().endswith("<start_event>"):
            case_id = binding[0][1].value  # the case_id is always [0] the first variable in the binding, the [1] token value of that, and [0] the case_id of the value.
            self.__case_arrivals[case_id] = time
        elif event.get_id().endswith("<end_event>"):
            case_id = binding[0][1].value[0]  # the case_id is always [0] the first variable in the binding, the [1] token value of that, and [0] the case_id of the value.
            waiting_time = time - self.__case_arrivals[case_id]
            total_time = self.__total_times[self.__nr_completed_cases]
            total_time += waiting_time
            self.__nr_completed_cases += 1
            self.times.append(time)
            self.__total_times.append(total_time)
            self.average_cycle_times.append(total_time/self.__nr_completed_cases)


class ProcessReporter(Reporter):
    """
    A reporter that heavily depends on the process prototypes (task, start_event, intermediate_event, end_event) to report on what happens.
    It assumes tasks are executed for cases that arrive via start_events and complete at end_events. It measures:
    - nr_started: the number of cases that started.
    - nr_completed: the number of cases that completed.
    - total_wait_time: the sum of waiting times of completed cases.
    - total_proc_time: the sum of processing times of completed cases.
    - total_cycle_time: the sum of cycle times of completed cases.
    - resource_busy_times: a mapping of resource_id -> the time the resource was busy during simulation.
    - activity_processing_times: a mapping of activity_id -> list of processing times.
    """

    # The names of the result sections
    WARMUP = "warmup"
    GENERAL = "general"
    RESOURCES = "resources"
    ACTIVITIES = "activities"

    def __init__(self, warmup_time=0):
        self.resource_busy_times = dict()  # mapping of resource_id -> the time the resource was busy during simulation.
        self.activity_processing_times = dict()  # mapping of activity_id -> list of processing times
        self.avg_cycle_time_over_time = []  # list of (time, avg_cycle_time) tuples
        self.nr_started = 0  # number of cases that started
        self.nr_completed = 0  # number of cases that completed
        self.total_wait_time = 0  # sum of waiting times of completed cases
        self.total_proc_time = 0  # sum of processing times of completed cases
        self.total_cycle_time = 0  # sum of cycle times of completed cases

        self.__status = dict()  # case_id -> (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change); time_last_busy_change is the time nr_busy_tasks last went from 0 to 1 or from 1 to 0
        self.__resource_start_times = dict()  # resource -> time
        self.__activity_start_times = dict()  # (case_id, activity_id) -> time
        self.__last_time = 0

        self.warmup_time = warmup_time

    def callback(self, timed_binding):
        (binding, time, event) = timed_binding
        self.__last_time = time
        if event.get_id().endswith("<start_event>"):
            case_id = binding[0][1].value  # the case_id is always [0] the first variable in the binding, the [1] token value of that, and [0] the case_id of the value.
            self.__status[case_id] = (0, time, 0, 0, time)
            if time > self.warmup_time:
                self.nr_started += 1
        elif event.get_id().endswith("<task:start>"):
            case_id = binding[0][1].value[0]  # the case_id is always [0] the first variable in the binding, the [1] token value of that, and [0] the case_id of the value.
            resource_id = binding[1][1].value  # the resource_id is always [1] the second variable in the binding, the [1] token value of that.
            self.__resource_start_times[resource_id] = time
            activity_id = event.get_id()[:event.get_id().index("<")]
            self.__activity_start_times[(case_id, activity_id)] = time
            (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change) = self.__status[case_id]
            if nr_busy_tasks == 0:
                sum_wait_times += time - time_last_busy_change
                time_last_busy_change = time
            nr_busy_tasks += 1
            self.__status[case_id] = (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change)
        elif event.get_id().endswith("<task:complete>"):
            case_id = binding[0][1].value[0][0]  # the case_id is always [0] the first variable in the binding, the [1] token value of that, and [0] the case_id of the value.
            resource_id = binding[0][1].value[1]  # the resource_id is always [0] the first variable in the binding, the [1] token value of that, and [1] the resource_id of the value.
            activity_id = event.get_id()[:event.get_id().index("<")]
            if time > self.warmup_time:
                if resource_id not in self.resource_busy_times.keys():
                    self.resource_busy_times[resource_id] = 0
                if self.__resource_start_times[resource_id] < self.warmup_time:
                    self.resource_busy_times[resource_id] += time - self.warmup_time
                else:
                    self.resource_busy_times[resource_id] += time - self.__resource_start_times[resource_id]
                if activity_id not in self.activity_processing_times.keys():
                    self.activity_processing_times[activity_id] = []
                self.activity_processing_times[activity_id].append(time - self.__activity_start_times[(case_id, activity_id)])
            del self.__resource_start_times[resource_id]
            del self.__activity_start_times[(case_id, activity_id)]
            (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change) = self.__status[case_id]
            if nr_busy_tasks == 1:
                sum_proc_times += time - time_last_busy_change
                time_last_busy_change = time
            nr_busy_tasks -= 1
            self.__status[case_id] = (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change)
        elif event.get_id().endswith("<end_event>"):
            case_id = binding[0][1].value[0]  # the case_id is always [0] the first variable in the binding, the [1] token value of that, and [0] the case_id of the value.
            (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change) = self.__status[case_id]
            del self.__status[case_id]
            if arrival_time > self.warmup_time:
                self.nr_completed += 1
                self.total_wait_time += sum_wait_times
                self.total_proc_time += sum_proc_times
                self.total_cycle_time += time - arrival_time
                self.avg_cycle_time_over_time.append((time, (self.total_cycle_time/self.nr_completed) if self.nr_completed > 0 else 0))

    def get_results(self):
        """
        Returns a dictionary of dictionaries::

            {
                warmup: {
                    avg_cycle_time_over_time: [(time, avg_cycle_time), ...]
                },
                general: {
                    nr_started: (int, float), # (average, stddev)
                    nr_completed: (int, float), # (average, stddev)
                    avg_wait_time: (float, float), # (average, stddev)
                    avg_proc_time: (float, float), # (average, stddev)
                    avg_cycle_time: (float, float) # (average, stddev)
                },
                resources: {
                    resource_id: {
                        utilization: (float, float) # (average, stddev)
                    },
                    ...
                },
                activities: {
                    activity_id: {
                        nr_started: (int, float), # (average, stddev)
                        nr_completed: (int, float), # (average, stddev)
                        avg_proc_time: (float, float) # (average, stddev)
                    },
                    ...
                }
            }
        """
        results = dict()
        
        warmup = dict()
        warmup["avg_cycle_time_over_time"] = self.avg_cycle_time_over_time
        results[ProcessReporter.WARMUP] = warmup

        general = dict()
        general["nr_started"] = self.nr_started
        general["nr_completed"] = self.nr_completed
        general["avg_wait_time"] = self.total_wait_time/self.nr_completed if self.nr_completed > 0 else 0
        general["avg_proc_time"] = self.total_proc_time/self.nr_completed if self.nr_completed > 0 else 0
        general["avg_cycle_time"] = self.total_cycle_time/self.nr_completed if self.nr_completed > 0 else 0
        results[ProcessReporter.GENERAL] = general

        resources = dict()
        # process the resources that are currently busy
        for resource_id in self.__resource_start_times.keys():
            self.resource_busy_times[resource_id] += self.__last_time - self.__resource_start_times[resource_id]

        self.__resource_start_times.clear()

        for resource_id in self.resource_busy_times.keys():
            utilization = self.resource_busy_times[resource_id]/(self.__last_time - self.warmup_time)
            resources[resource_id] = {"utilization": utilization}
        results[ProcessReporter.RESOURCES] = resources

        activities = dict()
        for activity_id in self.activity_processing_times.keys():
            times = self.activity_processing_times[activity_id]
            avg_time = sum(times)/len(times)
            activities[activity_id] = {
                "nr_started": len(times),
                "nr_completed": len(times),
                "avg_proc_time": avg_time
            }
        results[ProcessReporter.ACTIVITIES] = activities

        return results

    @staticmethod
    def aggregate_results(results_list):
        """
        Takes a list of results as returned by get_results and aggregates them into a single result.
        It does this by computing averages and standard deviations.
        It does this flexibly, i.e., it is unaware of the precise items in each section, but just computes averages and standard deviations of values.
        Note that a section is either a dictionary item -> value, or a dictionary item -> item -> value.
        """
        def aggregate_section_results(section_results_list):
            aggregated_section = {}
            for key in section_results_list[0].keys():
                values = [result[key] for result in section_results_list]
                avg = sum(values)/len(values)
                variance = sum((x - avg) ** 2 for x in values) / len(values)
                stddev = variance ** 0.5
                aggregated_section[key] = (avg, stddev)
            return aggregated_section

        aggregated_results = {}

        first_result = results_list[0]
        for section in first_result.keys():
            # check if the section contains items that are dictionaries themselves
            if isinstance(first_result[section], dict) and len(first_result[section]) > 0 and isinstance(next(iter(first_result[section].values())), dict):
                # section contains items that are dictionaries themselves
                aggregated_section = {}
                for item in first_result[section].keys():
                    aggregated_section[item] = aggregate_section_results([result[section][item] for result in results_list])
                aggregated_results[section] = aggregated_section
            elif isinstance(first_result[section], dict) and len(first_result[section]) > 0 and isinstance(next(iter(first_result[section].values())), list):
                # section contains a list of values, which typically is the warmup avg_cycle_time_over_time
                # we aggregate by simply taking the first result's list
                aggregated_results[section] = first_result[section]
            else:
                # section contains direct values
                aggregated_results[section] = aggregate_section_results([result[section] for result in results_list])

        return aggregated_results

    @staticmethod
    def possible_graphs():
        """
        Returns a dict of possible graphs that can be plotted based on the results.

        :return: a dict graph name -> graphing function
        """
        return {"Warmup": ProcessReporter.warmup_graph, "General statistics": ProcessReporter.general_statistics_graph, "Resource utilization": ProcessReporter.resource_utilization_graph, "Task processing times": ProcessReporter.task_processing_times_graph}

    @staticmethod
    def warmup_graph(aggregated_results, ax):
        """
        Plots the warmup graph on the given matplotlib axis.
        It plots the average cycle time over time.

        :param aggregated_results: the aggregated results as returned by aggregate_results.
        :param ax: the matplotlib axis to plot on.
        """
        times = [t for (t, avg_cycle_time) in aggregated_results[ProcessReporter.WARMUP]["avg_cycle_time_over_time"]]
        avg_cycle_times = [avg_cycle_time for (t, avg_cycle_time) in aggregated_results[ProcessReporter.WARMUP]["avg_cycle_time_over_time"]]
        ax.plot(times, avg_cycle_times)
        ax.set_xlabel("Time")
        ax.set_ylabel("Average Cycle Time")
        ax.set_title("Warmup: Average Cycle Time Over Time")

    @staticmethod
    def general_statistics_graph(aggregated_results, ax):
        """
        Plots the general statistics graph on the given matplotlib axis.
        Uses two y-axes, one for counts and one for times.

        :param aggregated_results: the aggregated results as returned by aggregate_results.
        :param ax: the matplotlib axis to plot on.
        """
        counts = [aggregated_results[ProcessReporter.GENERAL]["nr_started"][0], aggregated_results[ProcessReporter.GENERAL]["nr_completed"][0]]
        counts_stddev = [aggregated_results[ProcessReporter.GENERAL]["nr_started"][1], aggregated_results[ProcessReporter.GENERAL]["nr_completed"][1]]
        counts_whiskers = [1.96 * stddev for stddev in counts_stddev]

        times = [aggregated_results[ProcessReporter.GENERAL]["avg_wait_time"][0], aggregated_results[ProcessReporter.GENERAL]["avg_proc_time"][0], aggregated_results[ProcessReporter.GENERAL]["avg_cycle_time"][0]]
        times_stddev = [aggregated_results[ProcessReporter.GENERAL]["avg_wait_time"][1], aggregated_results[ProcessReporter.GENERAL]["avg_proc_time"][1], aggregated_results[ProcessReporter.GENERAL]["avg_cycle_time"][1]]
        times_whiskers = [1.96 * stddev for stddev in times_stddev]
        
        count_bars = ax.bar(["Nr started", "Nr completed"], counts, yerr=counts_whiskers, capsize=5, color='b', label='Counts')
        ax.set_ylabel("Counts", color='b')
        ax.tick_params(axis='y', labelcolor='b')
        
        # Add value labels on count bars
        for bar, value in zip(count_bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.1f}',
                   ha='center', va='bottom', color='b')

        ax2 = ax.twinx()
        time_bars = ax2.bar(["Avg wait time", "Avg proc time", "Avg cycle time"], times, yerr=times_whiskers, capsize=5, color='r', label='Times')
        ax2.set_ylabel("Times", color='r')
        ax2.tick_params(axis='y', labelcolor='r')
        
        # Add value labels on time bars
        for bar, value in zip(time_bars, times):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.2f}',
                    ha='center', va='bottom', color='r')

        ax.set_title("General Statistics")
        
    @staticmethod
    def task_processing_times_graph(aggregated_results, ax):
        """
        Plots the task processing times graph on the given matplotlib axis.

        :param aggregated_results: the aggregated results as returned by aggregate_results.
        :param ax: the matplotlib axis to plot on.
        """
        activity_ids = list(aggregated_results[ProcessReporter.ACTIVITIES].keys())
        activity_id_strs = [str(act_id) for act_id in activity_ids]
        avg_proc_times = [aggregated_results[ProcessReporter.ACTIVITIES][act_id]["avg_proc_time"][0] for act_id in activity_ids]
        # add whiskers for 95% confidence interval
        stddevs = [aggregated_results[ProcessReporter.ACTIVITIES][act_id]["avg_proc_time"][1] for act_id in activity_ids]
        whiskers = [1.96 * stddev for stddev in stddevs]
        ax.bar(activity_id_strs, avg_proc_times, yerr=whiskers, capsize=5)
        ax.set_xlabel("Activity")
        ax.set_ylabel("Average Processing Time")
        ax.set_title("Activity Processing Times")

    @staticmethod
    def resource_utilization_graph(aggregated_results, ax):
        """
        Plots the resource utilization graph on the given matplotlib axis.

        :param aggregated_results: the aggregated results as returned by aggregate_results.
        :param ax: the matplotlib axis to plot on.
        """
        resource_ids = list(aggregated_results[ProcessReporter.RESOURCES].keys())
        resource_id_strs = [str(res_id) for res_id in resource_ids]
        utilizations = [aggregated_results[ProcessReporter.RESOURCES][res_id]["utilization"][0] for res_id in resource_ids]
        # add whiskers for 95% confidence interval
        stddevs = [aggregated_results[ProcessReporter.RESOURCES][res_id]["utilization"][1] for res_id in resource_ids]
        whiskers = [1.96 * stddev for stddev in stddevs]
        ax.bar(resource_id_strs, utilizations, yerr=whiskers, capsize=5)
        ax.set_xlabel("Resource")
        ax.set_ylabel("Utilization")
        ax.set_title("Resource Utilization")

    def print_result(self, digits=3, digits_percentage=2):
        results = self.get_results()
        print("GENERAL STATISTICS")
        for key in results[ProcessReporter.GENERAL].keys():
            print(f"{key}: {round(results[ProcessReporter.GENERAL][key], digits)}")
        print("\nRESOURCE STATISTICS")
        for resource_id in results[ProcessReporter.RESOURCES].keys():
            print(f"Resource {resource_id}:")
            for key in results[ProcessReporter.RESOURCES][resource_id].keys():
                print(f"  {key}: {round(results[ProcessReporter.RESOURCES][resource_id][key], digits_percentage)}")
        print("\nACTIVITY STATISTICS")
        for activity_id in results[ProcessReporter.ACTIVITIES].keys():
            print(f"Activity {activity_id}:")
            for key in results[ProcessReporter.ACTIVITIES][activity_id].keys():
                print(f"  {key}: {round(results[ProcessReporter.ACTIVITIES][activity_id][key], digits)}")


class EventLogReporter(Reporter):
    """
    A reporter that heavily depends on the process prototypes (task, start_event, intermediate_event, end_event) to report on what happens.
    It stores the events that happen in an event log that can be mined with some process mining tool.
    As simulation time is a numerical value, some processing is done to convert simulation time
    into a time format that can be read and interpreted by a process mining tool. To that end,
    the timeunit in which simulation time is measured must be passed as well as the
    initial_time moment in calendar time from which the simulation time will be measured.
    A particular simulation_time moment will then be stored in the log as:
    initial_time + simulation_time timeunits. Data can also be reported on by specifying the
    corresponding data fields. The log will contain these data fields as additional columns in the order specified.
    Data will be taken from a case token from the BPMN prototype, which is always of the form (case_id, data).
    We recognize 3 forms of data:
    - basic datatype (int, float, str, bool): the start event and each task must have only one value and len(data_fields) == 1.
    - list or tuple of basic datatypes: the start event and each task must have len(data) == len(data_fields).
    - dictionary of basic datatypes: for each event, the data withs keys in data_fields will be included.

    :param filename: the name of the file in which the event log must be stored.
    :param timeunit: the :class:`.TimeUnit` of simulation time.
    :param initial_time: a datetime value.
    :param time_format: a datetime formatting string.
    :param data_fields: the data fields to report in the log.
    :param separator: the separator to use in the log.
    :param data_fields: a list of data field names to include in the log.
    """
    def __init__(self, filename, timeunit=TimeUnit.MINUTES, initial_time=datetime(2020, 1, 1), time_format="%Y-%m-%d %H:%M:%S.%f", separator=",", data_fields=None):
        self.task_start_times = dict()
        self.timeunit = timeunit
        self.initial_time = initial_time
        self.time_format = time_format
        self.logfile = open(filename, "wt")
        self.sep = separator        
        self.data_fields = data_fields
        self.logfile.write("case_id"+self.sep+"task"+self.sep+"resource"+self.sep+"start_time"+self.sep+"completion_time")
        if data_fields is not None:
            for field in data_fields:
                self.logfile.write(self.sep + field)
        self.logfile.write("\n")

    def displace(self, time):
        return self.initial_time + (timedelta(seconds=time) if self.timeunit == TimeUnit.SECONDS else timedelta(
            minutes=time) if self.timeunit == TimeUnit.MINUTES else timedelta(
            hours=time) if self.timeunit == TimeUnit.HOURS else timedelta(
            days=time) if self.timeunit == TimeUnit.DAYS else None)

    def process_data(self, data):
        if isinstance(data, (int, float, str, bool)):
            if len(self.data_fields) != 1:
                raise ValueError("Data is a basic datatype, but number of data fields specified in the EventLogReporter is not 1.")
            return [data]
        elif isinstance(data, (list, tuple)):
            if len(data) != len(self.data_fields):
                raise ValueError("Data is a list or tuple, but its length does not match the number of data fields specified in the EventLogReporter.")
            return list(data)
        elif isinstance(data, dict):
            return [data.get(field, "") for field in self.data_fields]
        else:
            raise ValueError("Data is of unsupported type for EventLogReporter.")

    def callback(self, timed_binding):
        (binding, time, event) = timed_binding        
        if event.get_id().endswith("<task:start>"):            
            case_id = binding[0][1].value[0]
            task = event.get_id()[:event.get_id().index("<")]
            self.task_start_times[(case_id, task)] = time
        elif event.get_id().endswith("<task:complete>"):
            case_id = binding[0][1].value[0][0]
            task = event.get_id()[:event.get_id().index("<")]
            resource = binding[0][1].value[1]
            if (case_id, task) in self.task_start_times.keys():
                self.logfile.write(str(case_id) + self.sep)
                self.logfile.write(task + self.sep)
                self.logfile.write(str(resource) + self.sep)
                self.logfile.write(self.displace(self.task_start_times[(case_id, task)]).strftime(self.time_format) + self.sep)
                self.logfile.write(self.displace(time).strftime(self.time_format))
                if self.data_fields is not None:
                    data = binding[0][1].value[0][1]
                    data_list = self.process_data(data)
                    for value in data_list:
                        self.logfile.write(self.sep + str(value))
                self.logfile.write("\n")
                self.logfile.flush()
                del self.task_start_times[(case_id, task)]
        elif event.get_id().endswith("<start_event>") or event.get_id().endswith("<intermediate_event>") or event.get_id().endswith("<end_event>"):
            if event.get_id().endswith("<start_event>"):
                case_id = binding[0][1].value
            else:
                case_id = binding[0][1].value[0]
            event = event.get_id()[:event.get_id().index("<")]
            self.logfile.write(str(case_id) + self.sep)
            self.logfile.write(event + self.sep)
            self.logfile.write(self.sep)
            self.logfile.write(self.displace(time).strftime(self.time_format) + self.sep)
            self.logfile.write(self.displace(time).strftime(self.time_format))
            if self.data_fields is not None:
                for _ in self.data_fields:
                    self.logfile.write(self.sep)
            self.logfile.write("\n")
            self.logfile.flush()

    def close(self):
        self.logfile.close()


class Replicator:
    """
    Class to handle the replication of simulation runs.
    The replicator uses a ProcessReporter to report on the replications.
    
    :param sim_problem: the simulation problem to replicate.
    :param duration: the duration of each replication.
    :param nr_replications: the number of replications to perform.
    :param callback: an optional callback function that is called after each replication with the percentage of replications completed, if it returns True, replications will continue, if it returns False, replications will stop.

    :return: a dictionary containing the result of each replication.
    """

    def __init__(self, sim_problem: SimProblem, duration: float, warmup: float = 0, nr_replications: int = 1, callback: Optional[Callable[[float], bool]] = None):
        self.sim_problem = sim_problem
        self.duration = duration
        self.warmup = warmup
        self.nr_replications = nr_replications
        self.callback = callback

    def run(self) -> Reporter:
        # Check if INITIAL_STATE checkpoint exists, create it if not
        INITIAL_STATE = "INITIAL_STATE"
        if INITIAL_STATE not in self.sim_problem.clock_checkpoints:
            self.sim_problem.store_checkpoint(INITIAL_STATE)

        # Prepare to collect results
        results = []

        # Run the replications
        for replication in range(self.nr_replications):
            # Restore to initial state
            self.sim_problem.restore_checkpoint(INITIAL_STATE)
            
            # Create a new ProcessReporter for this replication
            reporter = ProcessReporter(warmup_time=self.warmup)

            # Run the simulation with the reporter
            self.sim_problem.simulate(duration=self.duration, reporter=reporter)
            
            # Call the callback with percentage complete
            if self.callback is not None:
                percentage = ((replication + 1) / self.nr_replications) * 100
                if not self.callback(percentage):
                    break
            
            # Store the results
            results.append(reporter.get_results())
        
        self.sim_problem.restore_checkpoint(INITIAL_STATE)
        # Aggregate results from all replications
        return ProcessReporter().aggregate_results(results)        


class BindingEventLogReporter(Reporter):
    """
    A reporter that exports an event log based on the timed bindings that occur during the simulation.
    Each binding is of the form (binding, time, event), where binding is a tuple of (variable, value).
    The event log that is produced has the columns: event, time, variable_1, variable_2, ...
    For each binding, a new row is added to the log with the corresponding event, time, and variable values.

    :param filename: the name of the file in which the event log must be stored.
    :param separator: the separator to use in the log.
    """
    EVENT_COLUMN_LABEL = "event"
    TIME_COLUMN_LABEL = "time"

    def __init__(self, filename, separator=","):
        self._filename = filename
        self._separator = separator
        self._events = []
        self._times = []
        self._data_fields = dict() # maps variable names to their values

    def callback(self, timed_binding):
        (binding, time, event) = timed_binding
        self._events.append(event.get_id())
        self._times.append(time)        
        # add variables that are in the binding (i.e., have a value)
        for (var, token) in binding:
            if var.get_id() not in self._data_fields.keys():
                self._data_fields[var.get_id()] = [None] * (len(self._events)-1)
            self._data_fields[var.get_id()].append(token.value)
        # add None values for variables that are not in the binding (i.e., do not have a value)
        # since all all variables must have the same length, we add None values for any missing entries
        for var in self._data_fields.keys():
            if len(self._data_fields[var]) != len(self._events):
                self._data_fields[var].append(None)

    def close(self):
        with open(self._filename, "wt") as logfile:
            logfile.write(self.EVENT_COLUMN_LABEL + self._separator + self.TIME_COLUMN_LABEL)
            for var in self._data_fields.keys():
                logfile.write(self._separator + var)
            logfile.write("\n")
            for i in range(len(self._events)):
                logfile.write("\"" + str(self._events[i]) + "\"" + self._separator + str(self._times[i]))
                for var in self._data_fields.keys():
                    logfile.write(self._separator)
                    if i < len(self._data_fields[var]):
                        val = self._data_fields[var][i]
                        # if val is a str, surround it with quotes
                        if isinstance(val, str):
                            val = "\"" + val + "\""
                        logfile.write(str(val))
                logfile.write("\n")