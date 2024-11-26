import AccountSummary from '../components/AccountSummary'
import Headlines from '../components/Headlines'
import TECalendar from '../components/TECalendar'
import FFCalendar from '../components/FFCalendar'
import React, { useState, useEffect } from 'react';
import endPoints from '../app/api';
import Button from '../components/Button';
import TitleHead from '../components/TitleHead';


function Home() {
    const [startDate, setStartDate] = useState(""); // Start date input
    const [endDate, setEndDate] = useState("");   // End date input
    const [calendarData, setCalendarData] = useState(null); // Calendar data from API
    const [loadingTE, setLoadingTE] = useState(false); // Loading state for TE Calendar

    const [ffstartDate, setffStartDate] = useState(""); // Start date input
    const [ffcalendarData, setffCalendarData] = useState(null); // Calendar data from API
    const [loadingFF, setLoadingFF] = useState(false); // Loading state for FF Calendar

    // Format date to desired format
    const formatDate = (date) => {
        if (!date) return "";
        const months = ["Jan.", "Feb.", "Mar.", "Apr.", "May.", "Jun.", "Jul.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec."];
        const [year, month] = date.split("-");
        const formattedMonth = months[parseInt(month, 10) - 1];
        return `${formattedMonth}${year}`
    };

    const formatDateForAPI = (date) => {
        if (!date) return "";
        const d = new Date(date);
        return `${d.toISOString().split(".")[0]}Z`; // Convert to ISO format and append 'Z'
    };

    const loadteCalendarData = async () => {
        if (!startDate || !endDate) {
            alert("Please select both start and end dates.");
            return;
        }
        const formattedStartDate = formatDateForAPI(startDate);
        const formattedEndDate = formatDateForAPI(endDate);

        setLoadingTE(true);
        try {
            const data = await endPoints.te_calendar(formattedStartDate, formattedEndDate);
            setCalendarData(data);
        } catch (error) {
            console.error("Error fetching calendar data:", error);
            alert("Failed to fetch calendar data.");
        } finally {
            setLoadingTE(false);
        }
    };

    const loadffCalendarData = async () => {
        if (!ffstartDate) {
            alert("Please select start.", ffstartDate);
            return;
        }
        const formattStartDate = formatDate(ffstartDate);

        setLoadingFF(true);
        try {
            const data = await endPoints.ff_calendar(formattStartDate);
            setffCalendarData(data);
            console.log(data);
        } catch (error) {
            console.error("Error fetching calendar data:", error);
            alert("Failed to fetch calendar data.");
        } finally {
            setLoadingFF(false);
        }
    };

    return (
        <div>
            <AccountSummary />
            <Headlines />

            <TitleHead title="TradingEconomics - Economic Calendar" />
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
                <Button text="Fetch Data" handleClick={loadteCalendarData} />
            </div>
            <TitleHead title="TradingEconomics Calendar Data" />
            {loadingTE ? <h1>Loading...</h1> : calendarData && <TECalendar data={calendarData} />}

            <TitleHead title="Forex Factory - Economic Calendar" />
            <div className="segment options">
                <div className="date-picker">
                    <label>
                        Start Date: 
                        <input 
                            type="date" 
                            value={ffstartDate} 
                            onChange={(e) => setffStartDate(e.target.value)}
                        />
                    </label>
                    <div></div>
                </div>
                <Button text="Fetch Data" handleClick={loadffCalendarData} />
            </div>
            <TitleHead title="Forex Factory Calendar Data" />
            {loadingFF ? <h1>Loading...</h1> : ffcalendarData && <FFCalendar data={ffcalendarData} />}
        </div>
    );
}

export default Home;
