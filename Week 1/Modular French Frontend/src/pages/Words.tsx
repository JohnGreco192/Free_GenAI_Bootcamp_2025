
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Settings } from "lucide-react";
import { Link } from "react-router-dom";
import { useState } from "react";

const Words = () => {
  const [searchTerm, setSearchTerm] = useState("");

  const words = [
    {
      id: 1,
      word: "Tabarnac",
      translation: "Darn!/Holy!",
      category: "Expressions",
      difficulty: "Common",
      pronunciation: "ta-bar-NAK",
      usage: "Strong expression of surprise or frustration"
    },
    {
      id: 2,
      word: "Dépanneur",
      translation: "Convenience store",
      category: "Daily Life", 
      difficulty: "Essential",
      pronunciation: "day-pan-NŒUR",
      usage: "Small local store for quick purchases"
    },
    {
      id: 3,
      word: "Chum",
      translation: "Boyfriend/Friend",
      category: "Relationships",
      difficulty: "Common",
      pronunciation: "TCHUM",
      usage: "Informal term for boyfriend or close friend"
    },
    {
      id: 4,
      word: "Tuque",
      translation: "Winter hat/Beanie",
      category: "Clothing",
      difficulty: "Essential",
      pronunciation: "TOUK",
      usage: "Knitted winter cap worn in cold weather"
    },
    {
      id: 5,
      word: "Pouding chômeur",
      translation: "Unemployed pudding",
      category: "Food",
      difficulty: "Cultural",
      pronunciation: "poo-DING cho-MŒUR",
      usage: "Traditional Quebec dessert created during economic hardship"
    },
    {
      id: 6,
      word: "Char",
      translation: "Car",
      category: "Transportation",
      difficulty: "Common",
      pronunciation: "CHAR",
      usage: "Informal Quebec term for automobile"
    }
  ];

  const getCategoryColor = (category: string) => {
    const colors = {
      "Expressions": "bg-red-100 text-red-800",
      "Daily Life": "bg-blue-100 text-blue-800", 
      "Relationships": "bg-pink-100 text-pink-800",
      "Clothing": "bg-purple-100 text-purple-800",
      "Food": "bg-green-100 text-green-800",
      "Transportation": "bg-yellow-100 text-yellow-800"
    };
    return colors[category as keyof typeof colors] || "bg-gray-100 text-gray-800";
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "Essential": return "bg-green-100 text-green-800";
      case "Common": return "bg-yellow-100 text-yellow-800";
      case "Cultural": return "bg-red-100 text-red-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const filteredWords = words.filter(word =>
    word.word.toLowerCase().includes(searchTerm.toLowerCase()) ||
    word.translation.toLowerCase().includes(searchTerm.toLowerCase()) ||
    word.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Quebec French Vocabulary
          </h1>
          <p className="text-xl text-gray-600">
            Explore and manage your Quebec French word collection
          </p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700">
          <BookOpen className="h-4 w-4 mr-2" />
          Add New Word
        </Button>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5" />
            <span>Search & Filter</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex space-x-4">
            <div className="flex-1">
              <Input
                placeholder="Search words, translations, or categories..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full"
              />
            </div>
            <Button variant="outline">Filter by Category</Button>
            <Button variant="outline">Filter by Difficulty</Button>
          </div>
        </CardContent>
      </Card>

      {/* Words Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredWords.map((word) => (
          <Card key={word.id} className="border-blue-200 hover:shadow-lg transition-all duration-200 hover:border-blue-300">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-xl text-blue-700 mb-1">
                    {word.word}
                  </CardTitle>
                  <CardDescription className="text-lg font-medium text-gray-700">
                    {word.translation}
                  </CardDescription>
                  <p className="text-sm text-gray-500 mt-1">
                    /{word.pronunciation}/
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex flex-wrap gap-2">
                <Badge className={getCategoryColor(word.category)}>
                  {word.category}
                </Badge>
                <Badge className={getDifficultyColor(word.difficulty)}>
                  {word.difficulty}
                </Badge>
              </div>
              <p className="text-sm text-gray-600 leading-relaxed">
                {word.usage}
              </p>
              <div className="pt-2">
                <Button asChild variant="outline" className="w-full">
                  <Link to={`/words/${word.id}`}>
                    View Details
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="text-center">
          <CardContent className="pt-6">
            <div className="text-3xl font-bold text-blue-600 mb-2">342</div>
            <p className="text-sm text-gray-600">Total Words</p>
          </CardContent>
        </Card>
        <Card className="text-center">
          <CardContent className="pt-6">
            <div className="text-3xl font-bold text-green-600 mb-2">189</div>
            <p className="text-sm text-gray-600">Mastered</p>
          </CardContent>
        </Card>
        <Card className="text-center">
          <CardContent className="pt-6">
            <div className="text-3xl font-bold text-yellow-600 mb-2">98</div>
            <p className="text-sm text-gray-600">Learning</p>
          </CardContent>
        </Card>
        <Card className="text-center">
          <CardContent className="pt-6">
            <div className="text-3xl font-bold text-red-600 mb-2">55</div>
            <p className="text-sm text-gray-600">New</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Words;
