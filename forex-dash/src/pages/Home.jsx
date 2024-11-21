import AccountSummary from '../components/AccountSummary'
import Headlines from '../components/Headlines'
import Calendar from '../components/Calendar'
import React, { useState, useEffect } from 'react';
import endPoints from '../app/api';
import Button from '../components/Button';
import TitleHead from '../components/TitleHead';


function Home() {
    const [startDate, setStartDate] = useState(""); // Start date input
    const [endDate, setEndDate] = useState("");   // End date input
    const [calendarData, setCalendarData] = useState(null); // Calendar data from API
    const [loading, setLoading] = useState(true); // Loading state

    const formatDateForAPI = (date) => {
        if (!date) return "";
        const d = new Date(date);
        return `${d.toISOString().split(".")[0]}Z`; // Convert to ISO format and append 'Z'
    };

    useEffect(() => {
        setLoading(false); // Initialize UI without fetching data yet
    }, []);

    const loadCalendarData = async () => {
        if (!startDate || !endDate) {
            alert("Please select both start and end dates.");
            return;
        }


        const formattedStartDate = formatDateForAPI(startDate);
        const formattedEndDate = formatDateForAPI(endDate);

        console.log("Fetching data with:", formattedStartDate, formattedEndDate);

        setLoading(true);
        try {
            const data = await endPoints.calendar(formattedStartDate, formattedEndDate);
            setCalendarData(data);
        } catch (error) {
            console.error("Error fetching calendar data:", error);
            alert("Failed to fetch calendar data.");
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <h1>Loading...</h1>;

    return (
        <div>

            <AccountSummary />
            <Headlines />

            <TitleHead title="Economic Calendar" />
            <div className="segment options">
                <div className="date-picker">
                    <label>
                        Start Date: 
                        <input 
                            type="date" 
                            value={startDate} 
                            onChange={(e) => setStartDate(e.target.value)} 
                        />
                    </label>
                    <label>
                        End Date: 
                        <input 
                            type="date" 
                            value={endDate} 
                            onChange={(e) => setEndDate(e.target.value)} 
                        />
                    </label>
                    <div></div>
                </div>
                <Button text="Fetch Data" handleClick={loadCalendarData} />
            </div>
            <TitleHead title="Calendar Data" />
            {calendarData && <Calendar data={calendarData} />}
        </div>
    );
}

export default Home;
