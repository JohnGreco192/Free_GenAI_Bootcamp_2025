
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { BookOpen, Activity, Calendar, Settings } from "lucide-react";
import { Link, useParams } from "react-router-dom";

const GroupDetail = () => {
  const { id } = useParams();
  
  // Mock data - in real app this would come from API
  const group = {
    id: 1,
    name: "Quebec Swear Words",
    description: "Essential Quebec expressions and their cultural context - understand the colorful language that makes Quebec French unique",
    wordCount: 15,
    category: "Expressions",
    difficulty: "Intermediate",
    progress: 75,
    lastStudied: "2 days ago",
    created: "2 weeks ago",
    color: "bg-red-500",
    words: [
      { id: 1, word: "Tabarnac", translation: "Darn!/Holy!", mastery: 85, lastReviewed: "1 day ago" },
      { id: 2, word: "Câlice", translation: "Damn!", mastery: 92, lastReviewed: "2 days ago" },
      { id: 3, word: "Crisse", translation: "Christ!/Damn!", mastery: 78, lastReviewed: "3 days ago" },
      { id: 4, word: "Osti", translation: "Host!/Damn!", mastery: 65, lastReviewed: "1 week ago" },
      { id: 5, word: "Sacrament", translation: "Damn!", mastery: 70, lastReviewed: "5 days ago" },
      { id: 6, word: "Viarge", translation: "Holy Virgin!", mastery: 55, lastReviewed: "1 week ago" }
    ],
    studyHistory: [
      { date: "2024-01-15", activity: "Flashcard Review", score: 85, duration: "15 min" },
      { date: "2024-01-12", activity: "Context Practice", score: 78, duration: "20 min" },
      { date: "2024-01-10", activity: "Pronunciation", score: 92, duration: "12 min" }
    ]
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "Beginner": return "bg-green-100 text-green-800";
      case "Intermediate": return "bg-yellow-100 text-yellow-800";
      case "Advanced": return "bg-red-100 text-red-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const getCategoryColor = (category: string) => {
    return "bg-red-100 text-red-800"; // For expressions
  };

  const getMasteryColor = (mastery: number) => {
    if (mastery >= 80) return "text-green-600";
    if (mastery >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link to="/groups" className="text-blue-600 hover:text-blue-700 text-sm mb-2 block">
            ← Back to Word Groups
          </Link>
          <div className="flex items-center space-x-4 mb-4">
            <div className={`p-3 rounded-lg ${group.color}`}>
              <BookOpen className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                {group.name}
              </h1>
              <div className="flex items-center space-x-3">
                <Badge className={getCategoryColor(group.category)}>
                  {group.category}
                </Badge>
                <Badge className={getDifficultyColor(group.difficulty)}>
                  {group.difficulty}
                </Badge>
                <span className="text-gray-500">{group.wordCount} words</span>
              </div>
            </div>
          </div>
          <p className="text-lg text-gray-600 max-w-3xl">
            {group.description}
          </p>
        </div>
        <div className="flex space-x-3">
          <Button className="bg-blue-600 hover:bg-blue-700">
            <Activity className="h-4 w-4 mr-2" />
            Start Study Session
          </Button>
          <Button variant="outline">
            <Settings className="h-4 w-4 mr-2" />
            Edit Group
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-3 space-y-6">
          {/* Progress Overview */}
          <Card>
            <CardHeader>
              <CardTitle>Group Progress</CardTitle>
              <CardDescription>Your mastery of this word group</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600 mb-1">{group.progress}%</div>
                  <p className="text-sm text-gray-600">Overall Progress</p>
                  <Progress value={group.progress} className="mt-2" />
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600 mb-1">
                    {group.words.filter(w => w.mastery >= 80).length}
                  </div>
                  <p className="text-sm text-gray-600">Words Mastered</p>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-yellow-600 mb-1">
                    {group.words.filter(w => w.mastery < 80).length}
                  </div>
                  <p className="text-sm text-gray-600">Need Practice</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Words in Group */}
          <Card>
            <CardHeader>
              <CardTitle>Words in This Group</CardTitle>
              <CardDescription>All Quebec expressions in this collection</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {group.words.map((word, index) => (
                  <div key={word.id} className="flex items-center justify-between p-4 rounded-lg bg-blue-50 border border-blue-100 hover:bg-blue-100 transition-colors">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900">{word.word}</h4>
                          <p className="text-sm text-gray-600">{word.translation}</p>
                        </div>
                        <div className="text-center">
                          <div className={`text-lg font-bold ${getMasteryColor(word.mastery)}`}>
                            {word.mastery}%
                          </div>
                          <p className="text-xs text-gray-500">Mastery</p>
                        </div>
                        <div className="text-center">
                          <p className="text-sm text-gray-600">{word.lastReviewed}</p>
                          <p className="text-xs text-gray-500">Last reviewed</p>
                        </div>
                      </div>
                    </div>
                    <div className="flex space-x-2 ml-4">
                      <Button asChild variant="outline" size="sm">
                        <Link to={`/words/${word.id}`}>
                          View
                        </Link>
                      </Button>
                      <Button variant="outline" size="sm">
                        <Activity className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Study History */}
          <Card>
            <CardHeader>
              <CardTitle>Study History</CardTitle>
              <CardDescription>Your recent study sessions with this group</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {group.studyHistory.map((session, index) => (
                  <div key={index} className="flex items-center justify-between p-4 rounded-lg bg-gray-50 border border-gray-200">
                    <div className="flex items-center space-x-4">
                      <Calendar className="h-5 w-5 text-blue-600" />
                      <div>
                        <h4 className="font-medium text-gray-900">{session.activity}</h4>
                        <p className="text-sm text-gray-600">{session.date} • {session.duration}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-blue-600">{session.score}%</div>
                      <div className="text-xs text-gray-500">Score</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Stats */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Stats</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600 mb-1">{group.wordCount}</div>
                <p className="text-sm text-gray-600">Total Words</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600 mb-1">3</div>
                <p className="text-sm text-gray-600">Study Sessions</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600 mb-1">47</div>
                <p className="text-sm text-gray-600">Total Minutes</p>
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Study Options</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button className="w-full bg-blue-600 hover:bg-blue-700">
                <Activity className="h-4 w-4 mr-2" />
                Flashcard Review
              </Button>
              <Button variant="outline" className="w-full">
                <BookOpen className="h-4 w-4 mr-2" />
                Context Practice
              </Button>
              <Button variant="outline" className="w-full">
                <Calendar className="h-4 w-4 mr-2" />
                Pronunciation
              </Button>
              <Button variant="outline" className="w-full">
                <Settings className="h-4 w-4 mr-2" />
                Quiz Mode
              </Button>
            </CardContent>
          </Card>

          {/* Group Info */}
          <Card>
            <CardHeader>
              <CardTitle>Group Info</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Created:</span>
                <span className="font-medium">{group.created}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Last studied:</span>
                <span className="font-medium">{group.lastStudied}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Category:</span>
                <span className="font-medium">{group.category}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Difficulty:</span>
                <span className="font-medium">{group.difficulty}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default GroupDetail;
