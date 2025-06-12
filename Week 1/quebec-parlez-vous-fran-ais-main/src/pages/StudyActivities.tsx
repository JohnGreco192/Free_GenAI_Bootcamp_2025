
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Activity, Calendar } from "lucide-react";

const StudyActivities = () => {
  const activities = [
    {
      title: "Vocabulary Flash Cards",
      description: "Review your Quebec French words with interactive flashcards",
      difficulty: "Beginner",
      duration: "15-30 min",
      wordsCount: 25,
      icon: BookOpen,
      color: "bg-blue-500"
    },
    {
      title: "Quebec Expressions Quiz",
      description: "Test your knowledge of common Quebec expressions and their meanings",
      difficulty: "Intermediate",
      duration: "20-40 min", 
      wordsCount: 15,
      icon: Activity,
      color: "bg-green-500"
    },
    {
      title: "Cultural Context Matching",
      description: "Match Quebec words with their cultural context and usage",
      difficulty: "Advanced",
      duration: "25-45 min",
      wordsCount: 20,
      icon: Calendar,
      color: "bg-purple-500"
    },
    {
      title: "Pronunciation Practice",
      description: "Practice the unique pronunciation of Quebec French words",
      difficulty: "All Levels",
      duration: "10-20 min",
      wordsCount: 30,
      icon: BookOpen,
      color: "bg-orange-500"
    }
  ];

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "Beginner": return "bg-green-100 text-green-800";
      case "Intermediate": return "bg-yellow-100 text-yellow-800";
      case "Advanced": return "bg-red-100 text-red-800";
      default: return "bg-blue-100 text-blue-800";
    }
  };

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          Study Activities
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Choose an activity to enhance your Quebec French learning
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {activities.map((activity, index) => {
          const Icon = activity.icon;
          return (
            <Card key={index} className="border-blue-200 hover:shadow-xl transition-all duration-200 hover:border-blue-300">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${activity.color}`}>
                      <Icon className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{activity.title}</CardTitle>
                      <div className="flex items-center space-x-2 mt-2">
                        <Badge className={getDifficultyColor(activity.difficulty)}>
                          {activity.difficulty}
                        </Badge>
                        <span className="text-sm text-gray-500">{activity.duration}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <CardDescription className="text-base">
                  {activity.description}
                </CardDescription>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">
                    {activity.wordsCount} words included
                  </span>
                  <Button className="bg-blue-600 hover:bg-blue-700">
                    Start Activity
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Recent Sessions */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Study Sessions</CardTitle>
          <CardDescription>Your latest learning activities</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { activity: "Vocabulary Flash Cards", score: "85%", date: "Today", duration: "22 min" },
              { activity: "Quebec Expressions Quiz", score: "72%", date: "Yesterday", duration: "18 min" },
              { activity: "Cultural Context Matching", score: "91%", date: "2 days ago", duration: "35 min" }
            ].map((session, index) => (
              <div key={index} className="flex items-center justify-between p-4 rounded-lg bg-blue-50 border border-blue-100">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{session.activity}</h4>
                  <p className="text-sm text-gray-600">{session.date} • {session.duration}</p>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-blue-600">{session.score}</div>
                  <div className="text-xs text-gray-500">Score</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default StudyActivities;
