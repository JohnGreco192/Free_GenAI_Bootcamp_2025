import React, { useEffect, useState } from "react";
import { getGroups } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Settings, Activity } from "lucide-react";
import { Link } from "react-router-dom";

const Groups = () => {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getGroups()
      .then(data => setGroups(data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "Beginner": return "bg-green-100 text-green-800";
      case "Intermediate": return "bg-yellow-100 text-yellow-800";
      case "Advanced": return "bg-red-100 text-red-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const getCategoryColor = (category: string) => {
    const colors = {
      "Expressions": "bg-red-100 text-red-800",
      "Seasonal": "bg-blue-100 text-blue-800",
      "Food": "bg-green-100 text-green-800",
      "Urban": "bg-purple-100 text-purple-800",
      "Cultural": "bg-orange-100 text-orange-800",
      "Practical": "bg-indigo-100 text-indigo-800"
    };
    return colors[category as keyof typeof colors] || "bg-gray-100 text-gray-800";
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Word Groups
          </h1>
          <p className="text-xl text-gray-600">
            Organize your Quebec French vocabulary into themed collections
          </p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700">
          <BookOpen className="h-4 w-4 mr-2" />
          Create New Group
        </Button>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="text-center">
          <CardContent className="pt-6">
            <div className="text-3xl font-bold text-blue-600 mb-2">12</div>
            <p className="text-sm text-gray-600">Total Groups</p>
          </CardContent>
        </Card>
        <Card className="text-center">
          <CardContent className="pt-6">
            <div className="text-3xl font-bold text-green-600 mb-2">342</div>
            <p className="text-sm text-gray-600">Total Words</p>
          </CardContent>
        </Card>
        <Card className="text-center">
          <CardContent className="pt-6">
            <div className="text-3xl font-bold text-yellow-600 mb-2">68%</div>
            <p className="text-sm text-gray-600">Avg Progress</p>
          </CardContent>
        </Card>
        <Card className="text-center">
          <CardContent className="pt-6">
            <div className="text-3xl font-bold text-purple-600 mb-2">8</div>
            <p className="text-sm text-gray-600">Active Groups</p>
          </CardContent>
        </Card>
      </div>

      {/* Groups Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {groups.map((group) => (
          <Card key={group.id} className="border-blue-200 hover:shadow-xl transition-all duration-200 hover:border-blue-300">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-lg ${group.color}`}>
                    <BookOpen className="h-6 w-6 text-white" />
                  </div>
                  <div className="flex-1">
                    <CardTitle className="text-lg">{group.name}</CardTitle>
                    <div className="flex items-center space-x-2 mt-2">
                      <Badge className={getCategoryColor(group.category)}>
                        {group.category}
                      </Badge>
                      <Badge className={getDifficultyColor(group.difficulty)}>
                        {group.difficulty}
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <CardDescription className="text-base">
                {group.description}
              </CardDescription>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Progress</span>
                  <span className="font-medium">{group.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${group.progress}%` }}
                  ></div>
                </div>
              </div>
              
              <div className="flex items-center justify-between text-sm text-gray-600">
                <span>{group.wordCount} words</span>
                <span>Last studied: {group.lastStudied}</span>
              </div>
              
              <div className="flex space-x-2 pt-2">
                <Button asChild className="flex-1 bg-blue-600 hover:bg-blue-700">
                  <Link to={`/groups/${group.id}`}>
                    <BookOpen className="h-4 w-4 mr-2" />
                    View Group
                  </Link>
                </Button>
                <Button variant="outline" size="sm">
                  <Activity className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="sm">
                  <Settings className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Group Activity</CardTitle>
          <CardDescription>Your latest interactions with word groups</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { group: "Daily Conversations", action: "Completed study session", time: "2 hours ago", score: "92%" },
              { group: "Quebec Food & Drinks", action: "Added 3 new words", time: "1 day ago", score: "—" },
              { group: "Winter Vocabulary", action: "Reviewed flashcards", time: "3 days ago", score: "78%" }
            ].map((activity, index) => (
              <div key={index} className="flex items-center justify-between p-4 rounded-lg bg-blue-50 border border-blue-100">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{activity.group}</h4>
                  <p className="text-sm text-gray-600">{activity.action} • {activity.time}</p>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-blue-600">{activity.score}</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Groups;
