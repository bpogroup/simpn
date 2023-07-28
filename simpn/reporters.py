from datetime import datetime, timedelta
from enum import Enum, auto


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


class ProcessReporter(Reporter):
    """
    A reporter that heavily depends on the process prototypes (task, start_event, intermediate_event, end_event) to report on what happens.
    It assumes tasks are executed for cases that arrive via start_events and complete at end_events. It measures:
    - the number of started cases
    - the number of completed cases
    - the cycle time of completed cases (the time between their start and end event)
    - the processing time of completed cases (the time between a case's start and end during which a task was being performed)
    - the waiting time of completed cases (the time between a case's start and end during which no task was being performed)
    """

    def __init__(self):
        self.status = dict()  # case_id -> (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change); time_last_busy_change is the time nr_busy_tasks last went from 0 to 1 or from 1 to 0
        self.nr_started = 0
        self.nr_completed = 0
        self.total_wait_time = 0  # only of completed cases
        self.total_proc_time = 0  # only of completed cases
        self.total_cycle_time = 0  # only of completed cases

    def callback(self, timed_binding):
        (binding, time, event) = timed_binding
        if event.get_id().endswith("<start_event>"):
            case_id = binding[0][1].value  # the case_id is always [0] the first variable in the binding, the [1] token value of that, and [0] the case_id of the value.
            self.status[case_id] = (0, time, 0, 0, time)
            self.nr_started += 1
        elif event.get_id().endswith("<task:start>"):
            case_id = binding[0][1].value[0]  # the case_id is always [0] the first variable in the binding, the [1] token value of that, and [0] the case_id of the value.
            (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change) = self.status[case_id]
            if nr_busy_tasks == 0:
                sum_wait_times += time - time_last_busy_change
                time_last_busy_change = time
            nr_busy_tasks += 1
            self.status[case_id] = (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change)
        elif event.get_id().endswith("<task:complete>"):
            case_id = binding[0][1].value[0][0]  # the case_id is always [0] the first variable in the binding, the [1] token value of that, and [0] the case_id of the value.
            (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change) = self.status[case_id]
            if nr_busy_tasks == 1:
                sum_proc_times += time - time_last_busy_change
                time_last_busy_change = time
            nr_busy_tasks -= 1
            self.status[case_id] = (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change)
        elif event.get_id().endswith("<end_event>"):
            case_id = binding[0][1].value[0]  # the case_id is always [0] the first variable in the binding, the [1] token value of that, and [0] the case_id of the value.
            (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change) = self.status[case_id]
            del self.status[case_id]
            self.nr_completed += 1
            self.total_wait_time += sum_wait_times
            self.total_proc_time += sum_proc_times
            self.total_cycle_time += time - arrival_time

    def print_result(self):
        print("Nr. cases started:            ", self.nr_started)
        print("Nr. cases completed:          ", self.nr_completed)
        print("Avg. waiting time per case:   ", round(self.total_wait_time/self.nr_completed, 3))
        print("Avg. processing time per case:", round(self.total_proc_time/self.nr_completed, 3))
        print("Avg. cycle time per case:     ", round(self.total_cycle_time/self.nr_completed, 3))


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
    corresponding data fields. The names of these data fields must correspond to names of data fields as
    they appear in the problem.

    :param filename: the name of the file in which the event log must be stored.
    :param timeunit: the :class:`.TimeUnit` of simulation time.
    :param initial_time: a datetime value.
    :param time_format: a datetime formatting string.
    :param data_fields: the data fields to report in the log.
    """
    def __init__(self, filename, timeunit=TimeUnit.MINUTES, initial_time=datetime(2020, 1, 1), time_format="%Y-%m-%d %H:%M:%S.%f"):
        self.task_start_times = dict()
        self.timeunit = timeunit
        self.initial_time = initial_time
        self.time_format = time_format
        self.logfile = open(filename, "wt")
        self.logfile.write("case_id,task,resource,start_time,completion_time\n")

    def displace(self, time):
        return self.initial_time + (timedelta(seconds=time) if self.timeunit == TimeUnit.SECONDS else timedelta(
            minutes=time) if self.timeunit == TimeUnit.MINUTES else timedelta(
            hours=time) if self.timeunit == TimeUnit.HOURS else timedelta(
            days=time) if self.timeunit == TimeUnit.DAYS else None)

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
                self.logfile.write(str(case_id) + ",")
                self.logfile.write(task + ",")
                self.logfile.write(str(resource) + ",")
                self.logfile.write(self.displace(self.task_start_times[(case_id, task)]).strftime(self.time_format) + ",")
                self.logfile.write(self.displace(time).strftime(self.time_format))
                self.logfile.write("\n")
                self.logfile.flush()
                del self.task_start_times[(case_id, task)]
        elif event.get_id().endswith("<start_event>") or event.get_id().endswith("<intermediate_event>") or event.get_id().endswith("<end_event>"):
            if event.get_id().endswith("<start_event>"):
                case_id = binding[0][1].value
            else:
                case_id = binding[0][1].value[0]
            event = event.get_id()[:event.get_id().index("<")]
            self.logfile.write(str(case_id) + ",")
            self.logfile.write(event + ",")
            self.logfile.write(",")
            self.logfile.write(self.displace(time).strftime(self.time_format) + ",")
            self.logfile.write(self.displace(time).strftime(self.time_format))
            self.logfile.write("\n")
            self.logfile.flush()

    def close(self):
        self.logfile.close()