import React, { useEffect, useState } from "react";
import { getStudyActivities } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { BookOpen, Activity, Calendar, Settings } from "lucide-react";
import { Link } from "react-router-dom";

const Dashboard = () => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getStudyActivities()
      .then(data => setActivities(data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const stats = [
    { title: "Words Learned", value: "342", description: "Total vocabulary" },
    { title: "Study Sessions", value: "28", description: "This month" },
    { title: "Word Groups", value: "12", description: "Collections created" },
    { title: "Study Streak", value: "7", description: "Days in a row" },
  ];

  const recentActivities = [
    { type: "study", title: "Completed vocabulary review", time: "2 hours ago" },
    { type: "word", title: "Added 'tabarnac' to expressions", time: "4 hours ago" },
    { type: "group", title: "Created 'Quebec Slang' group", time: "1 day ago" },
  ];

  if (loading) return <div>Loading...</div>;

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          Bonjour! Welcome to your Quebec French Dashboard
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Continue your journey learning the beautiful language of Quebec
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <Card key={index} className="border-blue-200 hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                {stat.title}
              </CardTitle>
              <BookOpen className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-700">{stat.value}</div>
              <p className="text-xs text-gray-500">{stat.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Quick Actions */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5 text-blue-600" />
              <span>Quick Actions</span>
            </CardTitle>
            <CardDescription>
              Launch your favorite study activities
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Button asChild className="bg-blue-600 hover:bg-blue-700 h-16 flex-col space-y-2">
                <Link to="/study-activities">
                  <BookOpen className="h-6 w-6" />
                  <span>Start Study Session</span>
                </Link>
              </Button>
              <Button asChild variant="outline" className="h-16 flex-col space-y-2 border-blue-200 hover:bg-blue-50">
                <Link to="/words">
                  <BookOpen className="h-6 w-6" />
                  <span>Browse Vocabulary</span>
                </Link>
              </Button>
              <Button asChild variant="outline" className="h-16 flex-col space-y-2 border-blue-200 hover:bg-blue-50">
                <Link to="/groups">
                  <BookOpen className="h-6 w-6" />
                  <span>Manage Groups</span>
                </Link>
              </Button>
              <Button asChild variant="outline" className="h-16 flex-col space-y-2 border-blue-200 hover:bg-blue-50">
                <Link to="/sessions">
                  <Calendar className="h-6 w-6" />
                  <span>View Progress</span>
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Your latest learning progress</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {recentActivities.map((activity, index) => (
              <div key={index} className="flex items-start space-x-3 p-3 rounded-lg bg-blue-50">
                <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                  <p className="text-xs text-gray-500">{activity.time}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Progress Section */}
      <Card>
        <CardHeader>
          <CardTitle>Learning Progress</CardTitle>
          <CardDescription>Track your Quebec French mastery</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="font-medium">Vocabulary Mastery</span>
              <span className="text-gray-500">68%</span>
            </div>
            <Progress value={68} className="h-2" />
          </div>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="font-medium">Quebec Expressions</span>
              <span className="text-gray-500">45%</span>
            </div>
            <Progress value={45} className="h-2" />
          </div>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="font-medium">Cultural Context</span>
              <span className="text-gray-500">32%</span>
            </div>
            <Progress value={32} className="h-2" />
          </div>
        </CardContent>
      </Card>

      {/* Study Activities Section */}
      <Card>
        <CardHeader>
          <CardTitle>Study Activities</CardTitle>
          <CardDescription>Explore and manage your study activities</CardDescription>
        </CardHeader>
        <CardContent>
          <ul>
            {activities.map((activity: any) => (
              <li key={activity.id}>{activity.name}</li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;
