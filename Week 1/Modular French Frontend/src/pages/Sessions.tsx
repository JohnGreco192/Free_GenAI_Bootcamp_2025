
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { BookOpen, Activity, Calendar, Settings } from "lucide-react";

const Sessions = () => {
  const sessionStats = [
    { title: "Total Sessions", value: "147", description: "All time" },
    { title: "This Month", value: "28", description: "Study sessions" },
    { title: "Average Score", value: "82%", description: "Last 10 sessions" },
    { title: "Study Streak", value: "7", description: "Days in a row" },
  ];

  const recentSessions = [
    {
      id: 1,
      date: "2024-01-20",
      time: "14:30",
      activity: "Vocabulary Flash Cards",
      group: "Quebec Swear Words",
      duration: "22 min",
      wordsStudied: 15,
      score: 85,
      status: "completed"
    },
    {
      id: 2,
      date: "2024-01-19",
      time: "09:15",
      activity: "Context Practice",
      group: "Daily Conversations",
      duration: "18 min",
      wordsStudied: 12,
      score: 92,
      status: "completed"
    },
    {
      id: 3,
      date: "2024-01-18",
      time: "20:45",
      activity: "Pronunciation Practice",
      group: "Quebec Food & Drinks",
      duration: "15 min",
      wordsStudied: 8,
      score: 78,
      status: "completed"
    },
    {
      id: 4,
      date: "2024-01-17",
      time: "16:20",
      activity: "Quiz Mode",
      group: "Winter Vocabulary",
      duration: "25 min",
      wordsStudied: 20,
      score: 88,
      status: "completed"
    },
    {
      id: 5,
      date: "2024-01-16",
      time: "11:30",
      activity: "Cultural Context",
      group: "Montreal Slang",
      duration: "30 min",
      wordsStudied: 18,
      score: 65,
      status: "completed"
    }
  ];

  const weeklyProgress = [
    { day: "Mon", sessions: 2, score: 85 },
    { day: "Tue", sessions: 1, score: 78 },
    { day: "Wed", sessions: 3, score: 92 },
    { day: "Thu", sessions: 1, score: 88 },
    { day: "Fri", sessions: 2, score: 82 },
    { day: "Sat", sessions: 1, score: 90 },
    { day: "Sun", sessions: 2, score: 87 }
  ];

  const getScoreColor = (score: number) => {
    if (score >= 90) return "text-green-600";
    if (score >= 80) return "text-blue-600";
    if (score >= 70) return "text-yellow-600";
    return "text-red-600";
  };

  const getActivityColor = (activity: string) => {
    const colors = {
      "Vocabulary Flash Cards": "bg-blue-100 text-blue-800",
      "Context Practice": "bg-green-100 text-green-800",
      "Pronunciation Practice": "bg-purple-100 text-purple-800",
      "Quiz Mode": "bg-orange-100 text-orange-800",
      "Cultural Context": "bg-red-100 text-red-800"
    };
    return colors[activity as keyof typeof colors] || "bg-gray-100 text-gray-800";
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Study Sessions
          </h1>
          <p className="text-xl text-gray-600">
            Track your Quebec French learning progress and review your study history
          </p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700">
          <Activity className="h-4 w-4 mr-2" />
          Start New Session
        </Button>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {sessionStats.map((stat, index) => (
          <Card key={index} className="border-blue-200 hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                {stat.title}
              </CardTitle>
              <Calendar className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-700">{stat.value}</div>
              <p className="text-xs text-gray-500">{stat.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Sessions */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Recent Study Sessions</CardTitle>
              <CardDescription>Your latest learning activities</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentSessions.map((session) => (
                  <div key={session.id} className="p-4 rounded-lg border border-blue-100 bg-blue-50 hover:bg-blue-100 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <Badge className={getActivityColor(session.activity)}>
                            {session.activity}
                          </Badge>
                          <span className="text-sm text-gray-500">
                            {session.date} at {session.time}
                          </span>
                        </div>
                        <h4 className="font-medium text-gray-900 mb-1">
                          {session.group}
                        </h4>
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          <span>{session.duration}</span>
                          <span>•</span>
                          <span>{session.wordsStudied} words</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`text-2xl font-bold ${getScoreColor(session.score)}`}>
                          {session.score}%
                        </div>
                        <div className="text-xs text-gray-500">Score</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Performance Trends */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Trends</CardTitle>
              <CardDescription>Your learning progress over time</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="font-medium">Overall Improvement</span>
                  <span className="text-green-600">+12% this month</span>
                </div>
                <Progress value={75} className="h-3" />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600 mb-1">23</div>
                  <p className="text-sm text-gray-600">Best Streak</p>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600 mb-1">94%</div>
                  <p className="text-sm text-gray-600">Best Score</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Weekly Activity */}
          <Card>
            <CardHeader>
              <CardTitle>This Week</CardTitle>
              <CardDescription>Daily study activity</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {weeklyProgress.map((day, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className="text-sm font-medium w-8">{day.day}</span>
                      <div className="flex space-x-1">
                        {Array.from({ length: day.sessions }).map((_, i) => (
                          <div key={i} className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        ))}
                      </div>
                    </div>
                    <div className={`text-sm font-medium ${getScoreColor(day.score)}`}>
                      {day.score}%
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button className="w-full bg-blue-600 hover:bg-blue-700">
                <Activity className="h-4 w-4 mr-2" />
                Resume Last Session
              </Button>
              <Button variant="outline" className="w-full">
                <BookOpen className="h-4 w-4 mr-2" />
                Practice Weak Words
              </Button>
              <Button variant="outline" className="w-full">
                <Calendar className="h-4 w-4 mr-2" />
                Schedule Session
              </Button>
              <Button variant="outline" className="w-full">
                <Settings className="h-4 w-4 mr-2" />
                Export Progress
              </Button>
            </CardContent>
          </Card>

          {/* Goals */}
          <Card>
            <CardHeader>
              <CardTitle>Monthly Goals</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Study Sessions</span>
                  <span className="font-medium">28/30</span>
                </div>
                <Progress value={93} className="h-2" />
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>New Words</span>
                  <span className="font-medium">45/50</span>
                </div>
                <Progress value={90} className="h-2" />
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Average Score</span>
                  <span className="font-medium">82%/85%</span>
                </div>
                <Progress value={96} className="h-2" />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Sessions;
